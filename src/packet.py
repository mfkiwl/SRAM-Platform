#!/usr/bin/env python3
import hashlib
import struct
from abc import ABC
from abc import abstractmethod
from typing import List, Dict, Any


class Serializable(ABC):
    """
    Abstract class to represent a message sent in the network.
    Every Serializable object can be converted to bytes and created from bytes.
    """

    @classmethod
    def from_bytes(cls, blob: bytes):
        pass

    @abstractmethod
    def to_bytes(self):
        pass


def off_to_add(offset: int) -> str:
    """
    Convert an offset in memory to absolute memory address.

    The memory address is returned as a string.

    Args:
        offset

    Returns:
        String
    """
    return f"0x{0x20000000 + (offset * Packet.DATA_SIZE):08X}"


def calc_temp(temp: int, cal_30: int, cal_110: int) -> float:
    """
    Calculate the working temperature.

    Returns the working temperature in degrees celsius.

    Args:
      temp: Raw value from the temperature sensor.
      cal_30: Calibration value at 30 degrees celsius.
      cal_110: Calibration value at 110 degrees celsius.

    Returns:
      Float
    """
    return round(((110 - 30) / (cal_110 - cal_30)) * (temp - cal_30) + 40.0, 5)


def calc_vdd(vdd: int, vdd_cal: int) -> float:
    """
    Calculate the working voltage.

    Returns the reference voltage in volts.

    Args:
      vdd: Raw value from the voltage sensor.
      vdd_cal: Calibration value.

    Returns:
      Float
    """
    return round((3300 * vdd_cal / vdd) * 0.001, 5)


_CMD_TO_NAME = {
    1: "ACK",
    2: "PING",
    3: "READ",
    4: "WRITE",
    5: "SENSORS",
    6: "EXEC",
    255: "ERR",
}

_NAME_TO_CMD = {
    "ACK": 1,
    "PING": 2,
    "READ": 3,
    "WRITE": 4,
    "SENSORS": 5,
    "EXEC": 6,
    "ERR": 255,
}


class Packet(Serializable):
    """Packet used for the communication protocol.

    Attributes:
        command: Type of information the packet carries.
        pic: Position In Chain. The station is represented by 0.
        checksum: Checksum of the packet to ensure message integrity.
        options: Configuration for some of the commands.
            If the command is PING:
                +

            If the command is READ:
                + Offset of memory to read.

            If the command is WRITE:
                + Offset of memory to write.

        uid: Hex string representation of a device.
        Each ID is 24 bytes long plus the null terminator.

        data: Information carried by the packet.
        Its size is fixed to `DATA_SIZE`.

        __bytes: Bytes representation of the packet.

    Args:
        command:
        pic:
        uid:
        options:
        data:
        checksum:
    """

    DATA_SIZE = 512
    __fmt = f"<BBH25sI{DATA_SIZE}B"
    SIZE = struct.calcsize(__fmt)

    def __init__(
        self,
        command: int,
        pic: int = None,
        uid: str = None,
        options: int = None,
        data: List[int] = None,
        checksum: int = None,
    ):
        self.command = command
        self.pic = pic or 0
        self.options = options or 0x0
        self.uid = uid or "0" * 24
        self.data = data or ([0x7] * Packet.DATA_SIZE)
        if not checksum:
            self.__bytes = struct.pack(
                Packet.__fmt,
                self.command,
                self.pic,
                0x0,
                bytes(self.uid, "utf-8"),
                self.options,
                *self.data,
            )
            self.checksum = self.compute_checksum()
            self.__bytes = struct.pack(
                Packet.__fmt,
                self.command,
                self.pic,
                self.checksum,
                bytes(self.uid, "utf-8"),
                self.options,
                *self.data,
            )
        else:
            self.checksum = checksum
            self.__bytes = struct.pack(
                Packet.__fmt,
                self.command,
                self.pic,
                self.checksum,
                bytes(self.uid, "utf-8"),
                self.options,
                *self.data,
            )

    def compute_checksum(self) -> int:
        """
        Compute the checksum of a packet.

        Returns:
          Int.
        """
        return sum(bytearray(self.__bytes)) % 0xFFFF

    @classmethod
    def from_bytes(cls, blob: bytes):
        """
        Create a packet from bytes.

        Args:
          blob: Bytes representing the packet.

        Raises:
          ValueError: If the length of `blob` does not match `Packet.SIZE`.

        Returns:
          Packet.
        """
        if len(blob) != Packet.SIZE:
            error = f"Packet size {len(blob)} does not match {Packet.SIZE}"
            raise ValueError(error)
        (
            command,
            pic,
            checksum,
            uid,
            options,
            *data,
        ) = struct.unpack(Packet.__fmt, blob)
        return cls(
            command=command,
            pic=pic,
            checksum=checksum,
            uid=uid.decode("utf-8")[:-1],
            options=options,
            data=data,
        )

    def __str__(self) -> str:
        return (f"{_CMD_TO_NAME[self.command]} [{self.options}]"
                f"0x{self.checksum} P{self.pic} ({bytes(self.data)!r})")

    def __dict__(self):
        doc = {
            "pic": self.pic,
            "device": self.uid,
        }
        if _CMD_TO_NAME.get(self.command, "ERR") in ["READ", "WRITE"]:
            doc["data"] = bytes(self.data)
            doc["address"] = off_to_add(self.options)
            doc["checksum"] = self.checksum
        if _CMD_TO_NAME.get(self.command, "ERR") in ["SENSORS"]:
            # sensors = doc.update(self.extract_sensors())
            sensors = self.extract_sensors()
            doc["temperature"] = calc_temp(
                sensors["temp_raw"],
                sensors["temp_30_cal"],
                sensors["temp_110_cal"]
            )
            doc["voltage"] = calc_vdd(sensors["vdd_raw"], sensors["vdd_cal"])
        if _CMD_TO_NAME.get(self.command, "ERR") in ["ACK", "PING"]:
            doc["sram_size"] = self.options
        return doc

    def extract_sensors(self) -> dict:
        """
        temp_110_cal: 2 bytes
        temp_30_cal: 2 bytes
        temp_raw: 2 bytes
        vdd_cal: 2 bytes
        vdd_raw: 2 bytes
        """
        data = struct.unpack("<HHHHH", bytes(self.data[:10]))
        return {
            "temp_110_cal": data[0],
            "temp_30_cal": data[1],
            "temp_raw": data[2],
            "vdd_cal": data[3],
            "vdd_raw": data[4],
        }

    def to_bytes(self) -> bytes:
        """
        Return the bytes representation the packet.
        """
        return self.__bytes

    def create_uid(self, port: str = "/dev/ttyUSB0") -> str:
        """
        Create a unique md5 hash representing the device
        """
        hasher = hashlib.md5()
        hasher.update(bytes(self.pic))
        hasher.update(bytes(self.uid, "utf-8"))
        hasher.update(bytes(port, "utf-8"))
        return hasher.hexdigest()
