#!/usr/bin/env python
"""
WOOOT a pyrogram rewrite im crazyyy
"""

from pyrogram import Client
from configparser import ConfigParser

class alemiBot(Client):
    config = ConfigParser() # uggh doing it like this is not
    config.read("config.ini") # super nice but it'll do for now

    def __init__(self, name):
        super().__init__(
            name,
            plugins=dict(root=f"plugins/"),
            workdir="./",
            app_version="alemibot v0.1",)

    async def start(self):
        await super().start()
        print("> Bot started")

    async def stop(self, *args):
        await super().stop()
        print("> Bot stopped")

if __name__ == "__main__":
    app = alemiBot("debug")
    app.run()
