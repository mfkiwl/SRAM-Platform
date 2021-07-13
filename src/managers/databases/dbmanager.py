#!/usr/bin/env python3
from abc import ABC
from abc import abstractmethod
from typing import List
from typing import Union

from bson import ObjectId

Sample = Union[dict, List[dict]]
Query = Union[dict, str]
ID = Union[int, ObjectId]
IDs = Union[ID, List[ID]]


class DBManager(ABC):
    @abstractmethod
    def initialize(self) -> None:
        pass

    @abstractmethod
    def prepare_sample(self, sample: Sample, config: dict) -> Sample:
        pass

    @abstractmethod
    def insert(self, samples: Sample, config: dict) -> IDs:
        pass

    @abstractmethod
    def query(self, query: Query) -> Sample:
        pass

    @abstractmethod
    def query_reference(self, query: Query) -> Sample:
        pass

    @abstractmethod
    def clean_up(self) -> None:
        pass
