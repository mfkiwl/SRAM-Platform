#!/usr/bin/env python3
import json
import time

import requests
from datetime import datetime

DATE_FMT = "%d/%m/%Y %H:%M:%S"
import requests
import telebot

from private import TOKEN, CHAT_ID
# Bot related
bot = telebot.TeleBot(TOKEN, parse_mode=None)

from packet import Packet

STATION = "http://localhost:5000"

def timestamp():
    """
    Timestamp to keep track of the events
    """
    return datetime.now().strftime(DATE_FMT)

if __name__ == "__main__":
    # Turn on all ports
    res = requests.get( f"{STATION}/api/ports/power_on")
    res = json.loads(res.content)
    msg = f'{timestamp()}\n{res["message"].upper()}'
    bot.send_message(CHAT_ID, msg)
    time.sleep(30)

    # Register the devices
    requests.get(f"{STATION}/api/ports/register")
    res = requests.get(f"{STATION}/api/devices/register")
    ids, devices = [], []
    boards = json.loads(res.content)["data"]

    # Filter duplicate boards
    for dev in boards:
        if dev['device'] in ids:
            continue
        else:
            ids.append(dev['device'])
            devices.append(dev)

    devices_msg = "\n".join([d["device"] for d in devices])
    max_pic = max(d['pic'] for d in devices)
    devices_invert = list(filter(lambda d: d['pic'] <= (max_pic // 2), devices))
    msg = f'{timestamp()}\nREGISTERED DEVICES'
    msg = f'{msg}\nTOTAL: {len(devices)}\nINVERT: {len(devices_invert)}\n{devices_msg}'
    bot.send_message(CHAT_ID, msg)

    # Read memory of all boards
    msg = f'{timestamp()}\nREADING MEMORY'
    bot.send_message(CHAT_ID, msg)
    for device in devices:
        for off in range(device["sram_size"] // Packet.DATA_SIZE):
            res = requests.get(
                f"{STATION}/api/devices/read",
                json={"device": device["device"], "offset": off},
            )
            time.sleep(0.5)

    # Read sensors from all boards
    msg = f'{timestamp()}\nREADING SENSORS'
    bot.send_message(CHAT_ID, msg)
    for device in devices:
            res = requests.get( f"{STATION}/api/devices/sensors/{device['device']}")
            time.sleep(0.5)

    # Write values to all boards
    msg = f'{timestamp()}\nWRITING MEMORY'
    bot.send_message(CHAT_ID, msg)
    for device in devices_invert:
        for off in range(6, (device["sram_size"] // Packet.DATA_SIZE) - 6):
            res = requests.get(
                f"{STATION}/api/devices/write/invert",
                json={"device": device["device"], "offset": off},
            )
            time.sleep(0.5)

    msg = f'{timestamp()}\nFINISHED OPERATIONS'
    bot.send_message(CHAT_ID, msg)
