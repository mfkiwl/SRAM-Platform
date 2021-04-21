#!/usr/bin/env python
from abc import ABC
from abc import abstractmethod


class Logger(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def prepare_metrics(self, metrics: dict):
        pass

    @abstractmethod
    def log(self, metrics: dict):
        pass
