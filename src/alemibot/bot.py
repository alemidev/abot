import os
import sys
import asyncio
import subprocess
import logging
import inspect
from typing import List, Callable
from datetime import datetime
from configparser import ConfigParser

from setproctitle import setproctitle

from pyrogram import Client, ContinuePropagation, StopPropagation
from pyrogram.handlers.handler import Handler

from .util import get_username, Context
from .util.permission import Authenticator

class ReadyHandler(Handler):
	"""The Ready handler class. Used to handle client signaling being ready. It is intended to be used with
	:meth:`~pyrogram.Client.add_handler`
	For a nicer way to register this handler, have a look at the
	:meth:`~alemibot.alemiBot.on_ready` decorator.
	Parameters:
		callback (``callable``):
			Pass a function that will be called when the client is ready. It takes *(client)*
			as positional argument (look at the section below for a detailed description).
	Other parameters:
		client (:obj:`~pyrogram.Client`):
			The Client itself. Useful, for example, when you want to change the proxy before a new connection
			is established.
	"""
	def __init__(self, cb:Callable):
		super().__init__(cb)


class alemiBot(Client):
	start_time : datetime
	ctx : Context
	logger : logging.Logger
	config : ConfigParser

	auth : Authenticator
	sudoers : List[int]
	public : bool
	_lock : asyncio.Lock

	def __init__(self, name:str, app_version:str="0.5", workdir:str="./", config_file:str=None):
		super().__init__(
			name,
			workdir=workdir,
			app_version=app_version,
			config_file=f'{name}.ini' if config_file is None else config_file,
		)
		self.lock = asyncio.Lock()
		# Load config
		self.config = ConfigParser()
		alemiBot.config = self.config
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
		v_n = res.stdout.decode('utf-8').strip()
		self.app_version += "-" + ('???' if v_n.startswith('fatal') else v_n)

	async def _prepare_storage(self):
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

	async def start(self):
		await super().start()
		self.dispatcher.locks_list.append(self.lock)
		self.me = await self.get_me() # this is used to quickly parse /<cmd>@<who> format for commands
		setproctitle(f"alemiBot[{get_username(self.me)}]")
		self.logger.info("Running init callbacks")
		await self._prepare_storage()
		await self._process_ready_callbacks()
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
	
	@classmethod
	def on_ready(cls, group: int = 0) -> Callable:
		"""Decorator for handling client signaling being ready.
		This does the same thing as :meth:`~pyrogram.Client.add_handler` using the
		:obj:`~alemibot.bot.ReadyHandler`.
		Parameters:
			group (``int``, *optional*):
				The group identifier, defaults to 0.
		"""
		def decorator(func: Callable) -> Callable:
			if not hasattr(func, "handlers"):
				setattr(func, "handlers", [])
			func.handlers.append((ReadyHandler(func), group))
			return func
		return decorator

	async def _process_ready_callbacks(self):
		async with self.lock:
			for group in self.dispatcher.groups.values():
				for handler in group:
					args = None
					if isinstance(handler, ReadyHandler):
						try:
							if inspect.iscoroutinefunction(handler.callback):
								await handler.callback(self)
							else:
								await self.dispatcher.loop.run_in_executor(
									self.executor,
									handler.callback,
									self,
								)
						except StopPropagation:
							raise
						except ContinuePropagation:
							continue
						except Exception as e:
							self.logger.error(e, exc_info=True)

