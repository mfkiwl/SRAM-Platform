#!/usr/bin/env python3
import json
import time

import requests
from datetime import datetime

DATE_FMT = "%d/%m/%Y %H:%M:%S"
import requests
import telebot

from private import TOKEN, CHAT_ID
bot = telebot.TeleBot(TOKEN, parse_mode=None)

STATION = "http://localhost:5000"

if __name__ == "__main__":
    # Turn off all ports
    res = requests.get( f"{STATION}/api/ports/power_off")
    res = json.loads(res.content)
    msg = f'{datetime.now().strftime(DATE_FMT)}\n{res["message"].upper()}'
    bot.send_message(CHAT_ID, msg)
