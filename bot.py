#!/usr/bin/env python
"""
This is my take on Telegram userbots. I want this to be scalable so I made 
'module' classes which register handlers on the main bot. This file 
just makes the client, instantiates the classes, makes the help command 
and runs the client. All handlers are defined inside modules/
"""
import json

from telethon import TelegramClient, events

from modules.text import TextModules
from modules.dictionaries import DictionaryModules
from modules.files import FilesModules
from modules.meme import MemeModules
from modules.system import SystemModules
from modules.trigger import TriggerModules
from modules.management import ManagementModules

from util import can_react, set_offline

import logging
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s',
                    level=logging.WARNING)

config = None

with open("config.json") as f:
    config = json.load(f)

client = TelegramClient(
    config["NAME"], config["ID"],
    config["HASH"],
    proxy=None
)

with client:
    helptext = "" # lmao don't look at how helptext is handled inside the module classes

    helptext += DictionaryModules(client).helptext
    helptext += TextModules(client).helptext
    helptext += MemeModules(client).helptext
    helptext += FilesModules(client).helptext
    helptext += ManagementModules(client).helptext
    helptext += SystemModules(client).helptext
    helptext += TriggerModules(client).helptext

    # Help message
    @events.register(events.NewMessage(pattern=r"\.help"))
    async def helper(event):
        if can_react(event.chat_id):
            await event.reply("` ᚨᛚᛖᛗᛁᛒᛟᛏ v0.1`\n" +
                              "`→ .help ` print this\n" +
                                helptext +
                             f"\n__All cmds have a {config['cooldown']}s cooldown per chat__\n" +
                             f"__Commands with * are restricted__\n" +
                            "\nhttps://github.com/alemigliardi/alemibot")

    client.add_event_handler(helper)

    print(' [ Press Ctrl+C to stop this ]\n')
    client.run_until_disconnected()

print() # print a newline

