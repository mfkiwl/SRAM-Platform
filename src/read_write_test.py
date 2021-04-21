#!/usr/bin/env python3
import json
import time
from pprint import pprint

import requests

from packet import Packet

STATION = "http://localhost:5000"

if __name__ == "__main__":
    while True:
        # Register the devices
        res = requests.get(f"{STATION}/api/devices/register")
        devices = json.loads(res.content)["data"]
        max_pic = max(d['pic'] for d in devices)
        pprint(max_pic)
        devices_invert = list(filter(lambda d: d['pic'] <= (max_pic // 2), devices))
        pprint(devices)
        pprint(devices_invert)

        # Read memory of all boards
        for device in devices:
            for off in range(device["sram_size"] // Packet.DATA_SIZE):
                res = requests.get(
                    f"{STATION}/api/devices/read",
                    json={"device": device["device"], "offset": off},
                )
                print(json.loads(res.content)["message"])
                time.sleep(1)

        # Read sensors from all boards
        for device in devices:
                res = requests.get( f"{STATION}/api/devices/sensors/{device['device']}")
                print(json.loads(res.content))
                time.sleep(0.2)

        # Turn off all ports
        res = requests.get( f"{STATION}/api/ports/power_off")
        print(json.loads(res.content))
        time.sleep(60)

        # Turn on all ports
        res = requests.get( f"{STATION}/api/ports/power_on")
        print(json.loads(res.content))
        time.sleep(30)

        # Write values to all boards
        for device in devices_invert:
            for off in range(6, (device["sram_size"] // Packet.DATA_SIZE) - 6):
                res = requests.get(
                    f"{STATION}/api/devices/write/invert",
                    json={"device": device["device"], "offset": off},
                )
                print(json.loads(res.content)["message"])
                time.sleep(3)
