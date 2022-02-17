import os
import sys
import subprocess
import logging
from typing import List
from datetime import datetime
from configparser import ConfigParser

from setproctitle import setproctitle

from pyrogram import Client

from .util import get_username, Context
from .util.permission import Authenticator

class alemiBot(Client):
	start_time : datetime
	ctx : Context
	config : ConfigParser
	logger : logging.Logger

	auth : Authenticator
	sudoers : List[int]
	public : bool

	def __init__(self, name:str, app_version:str="0.5", workdir:str="./", config_file:str=None):
		super().__init__(
			name,
			workdir=workdir,
			app_version=app_version,
			config_file=f'{name}.ini' if config_file is None else config_file,
		)
		# Load config
		self.config = ConfigParser()
		self.config.read(f"{name}.ini")
		# Set useful attributes
		self.ctx = Context()
		self.logger = logging.getLogger(f"pyrogram.client.{name}")
		self.prefixes = list(self.config.get("customization", "prefixes", fallback="./"))
		self.start_time = datetime.now()
		# Load immutable perms from config
		self.auth = Authenticator(name)
		self.sudoers = [ int(uid.strip()) for uid in self.config.get("perms", "sudo", fallback="").split() ]
		self.public = self.config.getboolean("perms", "public", fallback=False) # util/permission
		# Get current commit hash and append to app version
		res = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
								stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
		self.app_version += "-" + res.stdout.decode('utf-8').strip()

	async def start(self):
		await super().start()
		self.me = await self.get_me() # this is used to quickly parse /<cmd>@<who> format for commands
		setproctitle(f"alemiBot[{get_username(self.me)}]")
		try: # TODO extend pyrogram Storage class to make fancy methods for custom stuff (like this)
			# Setup storage TODO make fancier
			self.storage.conn.execute("CREATE TABLE IF NOT EXISTS last_message ( chat_id LONG, message_id LONG );")
			msg = self.storage.conn.execute("SELECT * FROM last_message").fetchone()
			if msg:
				message = await self.get_messages(msg[0], msg[1])
				await message.edit(message.text.markdown + " [`OK`]")
		except Exception as e:
			self.logger.exception("Error editing restart message")
		finally:
			self.storage.conn.execute("DELETE FROM last_message")
		self.logger.info("Bot started")

	async def stop(self, block=True):
		buf = await super().stop(block)
		self.logger.info("Bot stopped")
		return buf

	async def restart(self):
		await self.stop()
		proc = ['python', '-m', 'alemibot'] + sys.argv[1:]
		self.logger.warning("Executing '%s'", str.join(' ', proc))
		os.execv(sys.executable, proc) # This will replace current process

