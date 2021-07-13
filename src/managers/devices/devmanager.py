#!/usr/bin/env python3
import sys
import time
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import Union

from serial import Serial
from serial.tools import list_ports

from packet import Packet
from packet import Serializable
from packet import Packet
from packet import Serializable
from serial import Serial
from serial.tools import list_ports


class DeviceManager(ABC):
    @abstractmethod
    def initialize(self):
        pass

    @abstractmethod
    def send(self, packet: Serializable):
        pass

    @abstractmethod
    def transmit(self, packet: Serializable, timeout: float):
        pass

    @abstractmethod
    def devices(self):
        pass


@dataclass
class Device:
    """
    Parameters of each device
    """

    uid: str
    pic: int
    state: str
    sram_size: int


class USBManager(DeviceManager):
    """
    USB Interface for the device manager.
    """

    def __init__(self, config: dict) -> None:
        self.__devices = []
        self.__ports = {}
        self.__config = config

    def send(self, packet: Serializable) -> None:
        """"""
        for _, port_info in self.__ports.items():
            ser = port_info["serial"]
            ser.flushInput()
            ser.write(packet.to_bytes())

    def receive(self) -> Union[List[Serializable], Serializable]:
        """"""
        packets = []
        time.sleep(0.5)

        for _, port_info in self.__ports.items():
            ser = port_info["serial"]
            msg = b""
            while ser.in_waiting:
                while len(msg) < Packet.SIZE:
                    msg += ser.read()
                packets.append(Packet.from_bytes(msg))
                msg = b""
            time.sleep(0.1)

        return packets[0] if len(packets) == 1 else packets

    def transmit(
        self, packet: Serializable, timeout=0.2
    ) -> Union[List[Serializable], Serializable]:
        """"""
        packets = []
        msg = b""
        for _, port_info in self.__ports.items():
            ser = port_info["serial"]
            ser.flushInput()
            ser.write(packet.to_bytes())
            ser.flushOutput()

            time.sleep(timeout)

            while ser.in_waiting:
                while len(msg) < Packet.SIZE:
                    msg += ser.read()
                packets.append(Packet.from_bytes(msg))
                msg = b""
                time.sleep(0.1)

        return packets[0] if len(packets) == 1 else packets

    @property
    def devices(self) -> List[Device]:
        """"""
        return self.__devices

    @devices.setter
    def devices(self, devices) -> None:
        """"""
        self.__devices = devices

    @property
    def ports(self) -> dict:
        """"""
        return self.__ports

    @ports.setter
    def ports(self, ports) -> None:
        """"""
        self.__ports = ports

    def initialize(self) -> None:
        """"""
        self.__ports = {}
        ports_paths = []

        if sys.platform.startswith("win"):
            ports_paths = list_ports.grep(".*COM.*")
        elif sys.platform.startswith("linux"):
            ports_paths = Path("/dev").glob("*USB*")

        for port in ports_paths:
            baudrate = self.__config['baudrate'].get(port.name, 350_000)
            ser = Serial(str(port), baudrate, timeout=None)
            port_info = {"state": "ON", "serial": ser}
            self.__ports[port.as_posix()] = port_info
