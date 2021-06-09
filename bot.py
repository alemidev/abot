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
from configparser import ConfigParser

from setproctitle import setproctitle

from pyrogram import Client

from util.getters import get_username

from plugins.core import edit_restart_message

class alemiBot(Client):
	config = ConfigParser() # uggh doing it like this kinda
	config.read("config.ini") #		ugly but it'll do for now
	sudoers = [ int(uid.strip()) for uid in config.get("perms", "sudo", fallback="").split() ]
	prefixes = config.get("customization", "prefixes", fallback="./")
	use_ssh = config.getboolean("customization", "useSsh", fallback=False)
	everyone_allowed = config.getboolean("perms", "public", fallback=False)
	allow_plugin_install = config.getboolean("perms", "allowPlugins", fallback=True)
	start_callbaks = []
	stop_callbacks = []

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

	@classmethod
	def on_start(cls, func):
		cls.start_callbaks.append(func)
		return func

	@classmethod
	def on_stop(cls, func):
		cls.stop_callbacks.append(func)
		return func

	async def start(self):
		await super().start()
		self.me = await self.get_me() # this is used to quickly parse /<cmd>@<who> format for commands
		setproctitle(f"alemiBot[{get_username(self.me)}]")
		if os.path.isfile("data/lastmsg.json"):
			await edit_restart_message(self) # if bot was restarted by an update, add [OK]
		logging.info("Bot started\n")
		for f in self.start_callbaks:
			await f(self)
		
	async def stop(self, block=True):
		for f in self.stop_callbacks:
			await f(self)
		buf = await super().stop(block)
		logging.info("Bot stopped\n")
		return buf
	
	async def restart(self):
		await self.stop()
		os.execv(__file__, sys.argv) # This will replace current process

if __name__ == "__main__":
	"""
	Default logging will only show the message on stdout (but up to INFO) 
	and show time + type + module + message in file (data/debug.log)
	"""
	setproctitle("alemiBot")
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	# create file handler which logs even debug messages
	fh = RotatingFileHandler('data/debug.log', maxBytes=1048576, backupCount=5) # 1MB files
	fh.setLevel(logging.INFO)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create formatter and add it to the handlers
	file_formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%b %d %Y %H:%M:%S")
	print_formatter = logging.Formatter("> %(message)s")
	fh.setFormatter(file_formatter)
	ch.setFormatter(print_formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(ch)

	app = alemiBot("alemibot")
	app.run()

