#!/usr/bin/env python3
from datetime import datetime
from typing import List
from typing import Union

import pymongo
from bson import ObjectId

from .dbmanager import DBManager
from .dbmanager import Query
from .dbmanager import Sample


class MongoDB(DBManager):
    """
    MongoDB Interface for the DBManager.

    Attributes:
      client:
    """

    def __init__(self, config: dict):
        super(MongoDB, self).__init__()
        url = f'mongodb://{config["host"]}:{config["port"]}/'
        self.__client = pymongo.MongoClient(url)
        self.__database = self.__client[config["name"]]
        self.__col = self.__database["samples"]

    def initialize(self):
        """"""
        pass

    def prepare_sample(self, sample: Sample, options: dict) -> Sample:
        """"""
        sample["timestamp"] = datetime.utcnow()
        return sample

    def insert(self, samples: Sample, config: dict) -> Union[ObjectId, List[ObjectId]]:
        """"""
        if not isinstance(samples, list):
            samples = [samples]

        ids = []
        for s in samples:
            sample = self.prepare_sample(s, config)
            super(MongoDB, self).insert(sample, config)
            ids.append(self.__col.insert_one(sample))
        return ids[0] if len(ids) == 1 else ids

    def query(self, query: Query) -> List[dict]:
        """"""
        return [sample for sample in self.__col.find(query)]

    def query_ref(
        self,
    ) -> dict:
        """"""
        return self.__col.find(query).sort("timestamp", pymongo.ASCENDING)[0]
