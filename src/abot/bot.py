import os
import sys
import asyncio
import subprocess
import logging

from typing import List
from datetime import datetime
from pathlib import Path
from configparser import ConfigParser

from setproctitle import setproctitle

from pyrogram import Client
from pyrogram.types import User
from pyrogram.storage import MemoryStorage
from pyrogram.enums import ParseMode

from .patches import OnReady, DocumentFileStorage
from .util import get_username, Context
from .util.permission import Authenticator
from .util.plugins import install_dependancies, install_plugin

class aBot(Client, OnReady):
	start_time : datetime
	ctx : Context
	me : User
	logger : logging.Logger
	config : ConfigParser

	auth : Authenticator
	storage : DocumentFileStorage
	sudoers : List[int]
	public : bool
	_lock : asyncio.Lock # for on_ready callback
	_allow_plugins : bool
	_preloaded_plugins: List[str]

	def __init__(
			self,
			name:str,
			config_file:str=None,
			allow_plugins:bool=False,
			sudoers:List[int]=None,
			prefixes:str=None,
			install:List[str]=None,
			pyrogram_logs:bool=False,
			**kwargs
	):
		# Load file config
		self.config = ConfigParser()
		self.config.read(config_file or f"{name}.ini")

		# Merge it with kwargs, with those taking precedence
		if self.config.has_section("pyrogram"):
			for k, v in self.config["pyrogram"].items():
				if k not in kwargs:
					# jank special cases for bools and ints, damn ini!
					if k == "ipv6":
						kwargs[k] = self.config.getboolean("pyrogram", "ipv6")
					elif k in ("workers", "sleep_threshold"):
						kwargs[k] = int(v)
					else:
						kwargs[k] = v

		if "session_string" in kwargs:
			storage = MemoryStorage(name, kwargs["session_string"])
		else:
			storage = DocumentFileStorage(name, Path(kwargs['workdir']) if 'workdir' in kwargs else Client.WORKDIR)

		if 'app_version' not in kwargs: # generate app version automatically
			# Get project version from setup.cfg
			setup_cfg = ConfigParser()
			setup_cfg.read("setup.cfg")
			v_base = setup_cfg.get('metadata', 'version', fallback="0")
			# Get current commit hash and append to app version
			res = subprocess.run(
				["git", "rev-parse", "--short", "HEAD"],
				stderr=subprocess.STDOUT, stdout=subprocess.PIPE
			)
			v_git = res.stdout.decode('utf-8').strip()
			if v_git.startswith("fatal"):
				v_git = '???'
			kwargs['app_version'] = f"{v_base}-{v_git}"

		if "plugins" not in kwargs:
			if self.config.has_section("plugins"):
				kwargs["plugins"] = dict(self.config["plugins"])
				if "include" in kwargs["plugins"]:
					kwargs["plugins"]["include"] = kwargs["plugins"]["include"].split()
				if "exclude" in kwargs["plugins"]:
					kwargs["plugins"]["exclude"] = kwargs["plugins"]["exclude"].split()
			else:
				kwargs["plugins"] = { "root": "plugins" }
		if 'root' not in kwargs['plugins']:
			kwargs['plugins']['root'] = 'plugins'

		super().__init__(
			name,
			in_memory=True,
			parse_mode=ParseMode.HTML,
			**kwargs
		)

		self.storage : DocumentFileStorage = storage # we need to override pyrogram storage since we can't pass it anymore
		self.session_name = name # override storage
		self._lock = asyncio.Lock()
		# Set useful attributes
		self.ctx = Context()
		self.logger = logging.getLogger(f"pyrogram.client.{name}")
		self.start_time = datetime.now()
		self.prefixes = prefixes or list(self.config.get("customization", "prefixes", fallback="./"))
		self._allow_plugins = allow_plugins or self.config.getboolean("perms", "allowPlugins", fallback=False)
		self._preloaded_plugins = install or []
		# Load immutable perms from config
		self.auth = Authenticator(name)
		self.sudoers = sudoers or [ int(uid.strip()) for uid in self.config.get("perms", "sudo", fallback="").split() ]
		self.public = self.config.getboolean("perms", "public", fallback=False) # util/permission
		# Silence some pyrogram logging prints
		if not pyrogram_logs:
			logging.getLogger('pyrogram.session').setLevel(logging.WARNING)  # So it's less spammy
			logging.getLogger('pyrogram.connection').setLevel(logging.WARNING)  # So it's less spammy
		# Install pre-loaded plugins

	async def _edit_last(self):
		if not isinstance(self.storage, DocumentFileStorage):
			return
		last = self.storage._get_last_message()
		if not last:
			return
		try:
			message = await self.get_messages(last[0], last[1])
			await message.edit(message.text.markdown + " [`OK`]")
		except Exception:
			self.logger.exception("Error editing restart message")

	async def start(self):
		for plugin in self._preloaded_plugins:
			try:
				await install_plugin(plugin)
				deps = await install_dependancies(plugin)
				self.logger.info("Installed %s (%d deps)", plugin, deps)
			except Exception:
				self.logger.exception("Could not preinstall plugin '%s'", plugin)
		self._preloaded_plugins = []
		await super().start()
		self.dispatcher.locks_list.append(self._lock)
		self.logger.info("Running init callbacks")
		self.me = await self.get_me() # this is used to quickly parse /<cmd>@<who> format for commands
		setproctitle(f"aBot[{get_username(self.me)}]")
		await self._edit_last()
		await self._process_ready_callbacks()
		self.logger.info("Bot started")

	async def stop(self, block=True):
		buf = await super().stop(block)
		self.logger.info("Bot stopped")
		return buf

	async def restart(self):
		await self.stop()
		proc = ['python', '-m', 'abot'] + sys.argv[1:]
		self.logger.warning("Executing '%s'", str.join(' ', proc))
		os.execv(sys.executable, proc) # This will replace current process
	
