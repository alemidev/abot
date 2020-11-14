#!/usr/bin/env python
"""
This is my take on Telegram userbots. I want this to be scalable so I made 
'module' classes which register handlers on the main bot. This file 
just makes the client, instantiates the classes, makes the help command 
and runs the client. All handlers are defined inside modules/
"""
import json
import time
import os
import sys

from telethon import TelegramClient, events

# TODO make a module loader
from modules.text import TextModules
from modules.search import SearchModules
from modules.files import FilesModules
from modules.meme import MemeModules
from modules.system import SystemModules
from modules.trigger import TriggerModules
from modules.management import ManagementModules
from modules.bully import BullyModules
from modules.logger import LoggerModules
from modules.math import MathModules

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

    helptext += LoggerModules(client).helptext
    helptext += SystemModules(client).helptext
    helptext += SearchModules(client).helptext
    helptext += TextModules(client).helptext
    helptext += MathModules(client).helptext
    helptext += MemeModules(client).helptext
    helptext += BullyModules(client).helptext
    helptext += FilesModules(client).helptext
    helptext += ManagementModules(client).helptext
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

    # async def edit_last(client):
    #     lastmsg = (await client.get_messages('me'))[0]
    #     if lastmsg.message.startswith(".update"):
    #         await lastmsg.edit(lastmsg.message + " [DONE]")
    
    client.loop.run_until_complete(client.send_message('me', '` → ᚨᛚᛖᛗᛁᛒᛟᛏ ` **online**'))

    print()
    print(' [ Press Ctrl+C to stop this ]\n')
    client.run_until_disconnected()

print()
try:
    print("→ Bot will self restart in 5 seconds, CTRL+C now to stop it")
    time.sleep(5)
    print()
    os.execv(__file__, sys.argv)
except KeyboardInterrupt as e:
    print()

