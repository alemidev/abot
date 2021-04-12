#!/usr/bin/env python
"""
WOOOT a pyrogram rewrite im crazyyy
"""
import os
import sys
import json
import subprocess
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from pyrogram import Client, idle
from configparser import ConfigParser

from pyrogram.raw.functions.account import UpdateStatus

class alemiBot(Client):
	config = ConfigParser() # uggh doing it like this kinda
	config.read("config.ini") #		ugly but it'll do for now
	prefixes = config.get("customization", "prefixes", fallback="./")
	allow_plugin_install = config.get("customization", "allowPlugins", fallback=True)

	def __init__(self, name):
		super().__init__(
			name,
			workdir="./",
			app_version="0.3",)
		self.start_time = datetime.now()
		# Get current commit hash and append to app version
		res = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
								stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		self.app_version += "-" + res.stdout.decode('utf-8').strip()

	async def set_offline(self):
		if not self.me.is_bot:
			await self.send(UpdateStatus(offline=True))

	async def start(self):
		await super().start()
		self.me = await self.get_me() # this is used to quickly parse /<cmd>@<who> format for commands
		try:
			with open("data/lastmsg.json", "r") as f:
				lastmsg = json.load(f)
			if lastmsg:
				message = await self.get_messages(lastmsg["chat_id"], lastmsg["message_id"])
				await message.edit(message.text.markdown + " [`OK`]")
				with open("data/lastmsg.json", "w") as f:
					json.dump({}, f)
		except:
			logging.exception("Error editing restart message")
		logging.warning("Bot started\n")
		
	async def stop(self, block=True):
		buf = await super().stop(block)
		logging.warning("Bot stopped\n")
		return buf
	
	async def restart(self):
		await self.stop()
		os.execv(__file__, sys.argv) # This will replace current process

if __name__ == "__main__":
	"""
	Default logging will only show the message on stdout (but up to INFO) 
	and show time + type + module + message in file (data/debug.log)
	"""
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	# create file handler which logs even debug messages
	fh = RotatingFileHandler('data/debug.log', maxBytes=1048576, backupCount=5) # 1MB files
	fh.setLevel(logging.INFO)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create formatter and add it to the handlers
	file_formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%H:%M:%S")
	print_formatter = logging.Formatter("> %(message)s")
	fh.setFormatter(file_formatter)
	ch.setFormatter(print_formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(ch)

	app = alemiBot("alemibot")
	app.run()

