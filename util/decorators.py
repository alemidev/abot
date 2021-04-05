import functools

from util.message import edit_or_reply

def report_error(lgr):
	"""
	This decorator will wrap the handler in a try/catch and 
	report of any raised exc to the user on telegram, while also
	logging to given logger
	"""
	def deco(func):
		@functools.wraps(func)
		async def innerWrapper(client, message):
			try:
				await func(client, message)
			except Exception as e:
				lgr.exception(f"Exception in '{func.__name__}'")
				await edit_or_reply(message, "`[!] → ` " + str(e))
		return innerWrapper
	return deco

def set_offline(func):
	"""Will set user back offline when function is done"""
	@functools.wraps(func)
	async def wrapper(client, message):
		await func(client, message)
		await client.set_offline()
	return wrapper