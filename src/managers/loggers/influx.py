#!/usr/bin/env python3
from datetime import datetime
from typing import List
from typing import Optional
from typing import Union

from influxdb import InfluxDBClient

from .logger import Logger


class InfluxDB(Logger):
    """
    InfluxDB Interface for the logger.
    """

    def __init__(self, config):
        self.__db_name = config["name"]
        self.__port = config["port"]
        self.__host = config["host"]
        self.__client = InfluxDBClient(host=self.__host, port=self.__port)

    def initialize(self):
        if len(self.__client.get_list_database()) <= 1:
            self.__client.create_database(self.__db_name)
        self.__client.switch_database(self.__db_name)

    def prepare_metrics(self, metrics: dict):
        metrics["time"] = datetime.utcnow()
        return metrics

    def log(self, metrics: dict):
        points = self.prepare_metrics(metrics)
        self.__client.write_points([points,])
