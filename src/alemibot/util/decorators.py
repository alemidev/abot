import functools
from typing import Callable, TYPE_CHECKING

from pyrogram.types import Message
from pyrogram.errors import ChatWriteForbidden, ChatSendMediaForbidden, FloodWait, SlowmodeWait
from pyrogram.raw.functions.account import UpdateStatus
from pyrogram.enums import ChatAction

from .message import edit_or_reply
from .getters import get_user, get_username, get_text

if TYPE_CHECKING:
	from ..bot import alemiBot

def report_error(lgr) -> Callable:
	"""Will report errors back to user

	This decorator will wrap the handler in a try/catch and
	report of any raised exc to the user on telegram, while also
	logging to given logger both command execution and eventual stacktrace
	"""
	def deco(func):
		@functools.wraps(func)
		async def wrapper(client, message, *args, **kwargs):
			author = get_username(get_user(message), log=True)
			try:
				lgr.info("[%s] running '%s'", author, func.__name__)
				await func(client, message, *args, **kwargs)
			except FloodWait as e:
				lgr.error("[%s] FloodWait too long (%d s), aborting", author, e.value)
			except SlowmodeWait as e:
				lgr.error("[%s] SlowmodeWait too long (%d s), aborting", author, e.value)
			except ChatWriteForbidden as e:
				try: # It may come from another chat, still try to report it
					await edit_or_reply(message, "`[!] → ` " + str(e))
				except ChatWriteForbidden: # Can't write messages here, prevent the double stacktrace
					lgr.error("[%s] Cannot send messages in this chat", author)
			except ChatSendMediaForbidden as e:
				try: # It may come from another chat, still try to report it
					await edit_or_reply(message, "`[!] → ` cannot send media in this chat")
					lgr.warning("[%s] Cannot send media in this chat", author)
				except Exception:
					lgr.exception("[%s] Cannot send media in this chat and failed to notify", author)
			except Exception as e:
				lgr.exception("[%s] exception in '%s' started by '%s'", author, func.__name__, get_text(message))
				await edit_or_reply(message, f"`[!] {type(e).__name__} → ` {str(e)}")
		return wrapper
	return deco

def set_offline(func) -> Callable:
	"""Will set user back offline when function is done"""
	@functools.wraps(func)
	async def wrapper(client:'alemiBot', message, *args, **kwargs):
		await func(client, message, *args, **kwargs)
		if not client.me.is_bot:
			await client.invoke(UpdateStatus(offline=True))
	return wrapper

def cancel_chat_action(func) -> Callable:
	"""Will cancel any ongoing chat action once handler is done"""
	@functools.wraps(func)
	async def wrapper(client:'alemiBot', message:Message, *args, **kwargs):
		await func(client, message, *args, **kwargs)
		await client.send_chat_action(message.chat.id, ChatAction.CANCEL)
	return wrapper
