#!/usr/bin/env python3
"""
To export the database to csv

>sqlite3 /path/to/database.db
sqlite> .headers on
sqlite> .mode csv
sqlite> .output file.csv
sqlite> SELECT uid, address, timestamp, data FROM samples;
sqlite> .quit
"""
from datetime import datetime
from sqlite3 import connect

import numpy as np

from .dbmanager import DBManager
from .dbmanager import IDs
from .dbmanager import Query
from .dbmanager import Sample


class SQLiteDB(DBManager):
    """
    SQLite Interface for the DBManager.
    """

    def __init__(self, config: dict):
        self.__conn = connect(config["file"], check_same_thread=False)
        self.__cur = self.__conn.cursor()

    def initialize(self):
        sql_setup = """
        CREATE TABLE IF NOT EXISTS
        samples(
        id INTEGER PRIMARY KEY ASC,
        device TEXT NOT NULL,
        pic INTEGER NOT NULL,
        address TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        data BLOB NOT NULL)
        """
        self.__cur.execute(sql_setup)
        self.__conn.commit()

    def insert(self, samples: Sample, config: dict) -> IDs:
        sql_insert = """
        INSERT INTO samples(device,pic,address,timestamp,data)
        VALUES (?,?,?,?,?)
        """

        if not isinstance(samples, list):
            samples = [samples]

        ids = []
        for sample in samples:
            sample = self.prepare_sample(sample, config)
            values = (
                sample["device"],
                sample["pic"],
                sample["address"],
                sample["timestamp"],
                sample["data"],
            )
            self.__cur.execute(sql_insert, values)
            ids.append(self.__cur.lastrowid)
        self.__conn.commit()
        return ids

    def query(self, query: Query) -> Sample:
        sql_query = f"""
        SELECT * FROM samples
        WHERE device in ({','.join(['?'] * len(devices))})
        AND
        WHERE address in ({','.join(['?'] * len(address))})
        """
        devices = query["device"]
        address = query["address"]
        rows = self.__cur.execute(sql_query, (devices, address))
        return rows.fetchall()

    def query_reference(self, query: Query):
        sql_search = """
        SELECT device,pic,address,timestamp,data FROM samples
        WHERE device = ? and address = ?
        ORDER BY timestamp ASC;
        """
        values = (query["device"], query["address"])
        row = self.__cur.execute(sql_search, values)
        row = row.fetchone()
        if not row:
            return None
        return {
            "device": row[0],
            "pic": row[1],
            "address": row[2],
            "timestamp": row[3],
            "data": np.array(list(row[4])).astype(np.uint8),
        }

    def prepare_sample(self, samples: Sample, config: dict) -> Sample:
        """"""
        if isinstance(samples, list):
            for sample in samples:
                sample["timestamp"] = datetime.utcnow().isoformat()
        else:
            samples["timestamp"] = datetime.utcnow().isoformat()
        return samples

    def clean_up(self):
        self.__conn.close()
