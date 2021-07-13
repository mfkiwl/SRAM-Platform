#!/usr/bin/env python
import threading
from datetime import datetime
from functools import wraps
from subprocess import run
from typing import List
from typing import Union

from managers import DBManager
from managers import Device
from managers import DeviceManager
from managers import Logger
from managers import Query
from managers import Sample
from packet import _NAME_TO_CMD
from packet import Packet


class LockedError(Exception):
    """Raised when the Station is carrying out a job"""


def power_on_ports(ports: Union[str, List[str]]):
    """
    Power on all devices
    """
    run(["ykushcmd", "-u", "a"])


def exclusive(fn):
    @wraps(fn)
    def inner(*args):
        pass

    return inner


class Station:
    """"""

    def __init__(
        self,
        config: dict,
        dev_manager: DeviceManager,
        samples_db: DBManager,
        logger: Logger,
    ):
        self.__config = config
        self.__lock = threading.Lock()

        self._dev_manager = dev_manager

        self._logger = logger
        self._samples_db = samples_db

        self._logger.initialize()
        self._samples_db.initialize()

        self.__uptime = datetime.utcnow()

        self._dev_manager.initialize()

    def exclusive(fn, *args):
        """Decorator used to prevent race conditions."""

        def fn(self, *args):
            if not self.__lock.acquire(False):
                raise LockedError
            try:
                res = fn(self, args)
            except TypeError:
                res = fn(self)
            finally:
                self.__lock.release()
            return res

        return fn

    def initialize(self):
        self._dev_manager.initialize()

    @property
    def ports(self):
        ports = []
        for port_name, port_info in self._dev_manager.ports.items():
            ports.append({"port": port_name, "state": port_info["state"]})
        return ports

    @property
    def devices(self) -> List[Device]:
        devs = []
        uids = []
        for dev in self._dev_manager.devices:
            if dev.uid in uids:
                continue
            else:
                devs.append(dev)
                uids.append(dev.uid)
        print(devs)
        return devs

    def status(self) -> dict:
        """
        Inform about the status of the station.

        Return:
          Dict
        """
        return {
                "uptime": self.__uptime,
                "ports": self.ports,
                "devices": self.devices
                }

    def cmd_ping(self, config: dict) -> Sample:
        """"""
        self._dev_manager.devices = []

        options = 1 if "device" in config else 0
        packet = Packet(
            _NAME_TO_CMD["PING"],
            options=options,
            uid=config.get("device", None),
        )
        # self._dev_manager.send(packet)
        # packets = self._dev_manager.receive()
        packets = self._dev_manager.transmit(packet)

        if isinstance(packets, Packet):
            packets = [packets]

        response = []
        devices = []
        ids = []
        for p in packets:
            if p.uid in ids:
                continue
            else:
                ids.append(p.uid)
                response.append(p.__dict__())
                devices.append(Device(p.uid, p.pic, "ON", p.options))
        self._dev_manager.devices = devices
        return response

    def cmd_read(self, config: dict) -> dict:
        """"""
        packet = Packet(
            _NAME_TO_CMD["READ"],
            pic=0,
            options=config["offset"],
            uid=config["device"],
        )
        # self._dev_manager.send(packet)
        # response = self._dev_manager.receive()
        response = self._dev_manager.transmit(packet, timeout=4)
        return response.__dict__() if response else None

    def cmd_write(self, config: dict) -> dict:
        """"""
        packet = Packet(
            _NAME_TO_CMD["WRITE"],
            pic=0,
            options=config["offset"],
            uid=config["device"],
            data=config["data"],
        )
        # self._dev_manager.send(packet)
        # response = self._dev_manager.receive()
        response = self._dev_manager.transmit(packet, timeout=4)
        return response.__dict__() if response else None

    def cmd_sensors(self, config: dict) -> Sample:
        packet = Packet(
            _NAME_TO_CMD["SENSORS"],
            pic=0,
            options=0,
            uid=config["device"],
        )
        # self._dev_manager.send(packet)
        # response = self._dev_manager.receive()
        response = self._dev_manager.transmit(packet, timeout=4)
        return response.__dict__() if response else None

    def ports_power_on(self, ports: Union[str, List[str]] = None):
        """
        Power on all ports.

        Args:

        Returns:
        """
        cmd = "ykushcmd -u a"
        run(cmd, shell=True)
        ports = self._dev_manager.ports
        for _, port_info in ports.items():
            port_info["state"] = "ON"
        self._dev_manager.ports = ports

        devices = self._dev_manager.devices
        for device in devices:
            device.state = "ON"
        self._dev_manager.devices = devices

    def ports_power_off(self, ports: Union[str, List[str]] = None):
        """
        Power down all ports.

        Args:

        Returns:
        """
        cmd = "ykushcmd -d a"
        run(cmd, shell=True)
        ports = self._dev_manager.ports
        for _, port_info in ports.items():
            port_info["state"] = "OFF"
        self._dev_manager.ports = ports

        devices = self._dev_manager.devices
        for device in devices:
            device.state = "OFF"
        self._dev_manager.devices = devices

    def insert_sample(self, sample: Sample, config: dict) -> None:
        """"""
        self._samples_db.insert(sample, config)

    def metrics_log(self, metrics: dict) -> None:
        """"""
        self._logger.log(metrics)

    def query_reference(self, query: Query) -> dict:
        """"""
        return self._samples_db.query_reference(query)
