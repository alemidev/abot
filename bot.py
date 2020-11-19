#!/usr/bin/env python
"""
WOOOT a pyrogram rewrite im crazyyy
"""
import os
import sys
from datetime import datetime
from pyrogram import Client, idle
from configparser import ConfigParser

class alemiBot(Client):
    config = ConfigParser() # uggh doing it like this kinda
    config.read("config.ini") #     ugly but it'll do for now
    prefixes = config.get("customization", "prefixes", fallback="./")

    def __init__(self, name):
        super().__init__(
            name,
            plugins=dict(root=f"plugins/"),
            workdir="./",
            app_version="alemibot v0.1",)
        self.start_time = datetime.now()

    async def start(self):
        await super().start()
        print("> Bot started\n")

    async def stop(self):
        await super().stop()
        print("\n> Bot stopped")
    
    async def restart(self):
        await self.stop()
        os.execv(__file__, sys.argv) # This will replace current process

if __name__ == "__main__":
    app = alemiBot("debug")
    app.run()

