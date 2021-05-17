import functools

from pyrogram.raw.functions.account import UpdateStatus

from util.message import edit_or_reply

def report_error(lgr):
	"""Will report errors back to user

	This decorator will wrap the handler in a try/catch and
	report of any raised exc to the user on telegram, while also
	logging to given logger both command execution and eventual stacktrace
	"""
	def deco(func):
		@functools.wraps(func)
		async def wrapper(client, message, *args, **kwargs):
			try:
				lgr.info("Running '%s'", func.__name__)
				await func(client, message, *args, **kwargs)
			except Exception as e:
				lgr.exception("Exception in '%s'", func.__name__)
				await edit_or_reply(message, "`[!] → ` " + str(e))
		return wrapper
	return deco

def set_offline(func):
	"""Will set user back offline when function is done"""
	@functools.wraps(func)
	async def wrapper(client, message, *args, **kwargs):
		await func(client, message, *args, **kwargs)
		if not client.me.is_bot:
			await client.send(UpdateStatus(offline=True))
	return wrapper

def cancel_chat_action(func):
	"""Will cancel any ongoing chat action once handler is done"""
	@functools.wraps(func)
	async def wrapper(client, message, *args, **kwargs):
		await func(client, message, *args, **kwargs)
		await client.send_chat_action(message.chat.id, "cancel")
	return wrapper
