#!/usr/bin/env python
"""
WOOOT a pyrogram rewrite im crazyyy
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pyrogram import Client, idle
from configparser import ConfigParser

from pyrogram.raw.functions.account import UpdateStatus

class alemiBot(Client):
    config = ConfigParser() # uggh doing it like this kinda
    config.read("config.ini") #     ugly but it'll do for now
    prefixes = config.get("customization", "prefixes", fallback="./")

    def __init__(self, name):
        super().__init__(
            name,
            workdir="./",
            app_version="0.2",)
        self.start_time = datetime.now()
        # Get current commit hash and append to app version
        res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True)
        self.app_version += "-" + res.stdout.decode('utf-8').strip()

    async def set_offline(self):
        await self.send(UpdateStatus(offline=True))

    async def start(self):
        await super().start()
        print("> Bot started\n")
        try:
            with open("data/lastmsg.json", "r") as f:
                m = json.load(f)
                message = await self.get_messages(m["chat_id"], m["message_id"])
                await message.edit(message.text.markdown + " [OK]")
            with open("data/lastmsg.json", "w") as f:
                json.dump({}, f)
        except:
            pass # ignore

    async def stop(self):
        await super().stop()
        print("\n> Bot stopped")
    
    async def restart(self):
        await self.stop()
        os.execv(__file__, sys.argv) # This will replace current process

if __name__ == "__main__":
    app = alemiBot("alemibot")
    app.run()

