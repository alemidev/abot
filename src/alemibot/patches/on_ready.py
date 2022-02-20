import inspect
from typing import Callable

from pyrogram import Client, ContinuePropagation, StopPropagation
from pyrogram.scaffold import Scaffold
from pyrogram.handlers.handler import Handler

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

class OnReady(Scaffold):
	def on_ready(self=None, group:int=0) -> Callable:
		"""Decorator for handling client signaling being ready.
		This does the same thing as :meth:`~pyrogram.Client.add_handler` using the
		:obj:`~alemibot.bot.ReadyHandler`. While only one pyrogram handler per group
		will trigger, all OnReady callbacks in each group will be called. Groups
		can be used to force a load order.
		Parameters:
			group (``int``, *optional*):
				The group identifier, defaults to 0.
		"""
		def decorator(func: Callable) -> Callable:
			handl = (ReadyHandler(func), group)
			if isinstance(self, Client):
				self.add_handler(handl)
			else:
				if not hasattr(func, "handlers"):
					setattr(func, "handlers", [])
				func.handlers.append(handl)
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

