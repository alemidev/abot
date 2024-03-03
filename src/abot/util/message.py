import asyncio
import logging
import functools

from time import time

from pyrogram.types import Message
from pyrogram import Client
from pyrogram.errors import ChatWriteForbidden, FloodWait
from pyrogram.enums import ChatAction, ParseMode

from .text import batchify
from .getters import get_text

def _catch_errors(fun):
	@functools.wraps(fun)
	async def wrapper(self, *args, **kwargs):
		try:
			await fun(self, args, kwargs)
		except FloodWait as e:
			logging.error("FloodWait too long (%d s), aborting", e.value)
		except ChatWriteForbidden:
			logging.error("Cannot write in this chat")
		except Exception:
			logging.exception("ignoring exception in '%s'", fun.__name__)
	return wrapper

class ProgressChatAction:
	"""Helper class for ongoing chat actions.
	Wraps information needed to send the chat action and provides either
	the ability to run the task in background and stop it when done, or to call
	a method which will not send another chat action until cooldown expired.
	Can be used as context manager.
	"""
	def __init__(
			self,
			client:Client,
			chat_id:int,
			action:ChatAction=ChatAction.TYPING,
			interval:float=4.75
	):
		self.client = client
		self.chat_id = chat_id
		self.action = action
		self.interval = interval
		self._running = False
		self.last = 0

	@_catch_errors
	async def _tick_task(self, *args, **kwargs):
		while self._running:
			self.last = time()
			await asyncio.gather(
				self.client.send_chat_action(self.chat_id, self.action),
				asyncio.sleep(self.interval)
			)

	@_catch_errors
	async def tick(self, *args, **kwargs): # args and kwargs so this can be used as progres callback for uploads
		"""If <interval> time has passed since last chat action, update last time and send a chat action"""
		if time() - self.last > self.interval:
			self.last = time()
			await self.client.send_chat_action(self.chat_id, self.action)

	def run(self) -> bool:
		"""Start a background task, sending a chat action every <interval> seconds.
		Won't start a new task if one is running. Returns True if a new task was started.
		"""
		if self._running:
			return False
		self._running = True
		asyncio.get_event_loop().create_task(self._tick_task())
		return True

	def stop(self):
		"""Stop the background task"""
		self._running = False

	def __enter__(self):
		self.run()
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()


def is_me(message:Message) -> bool:
	return message.outgoing or (
		message.from_user is not None 
		and message.from_user.is_self
		and message.via_bot is None  # can't edit messages from inline bots
	) or False

async def edit_or_reply(message:Message, text:str, separator:str="\n", nomentions:bool=False, *args, **kwargs) -> Message:
	"""Will edit provided message if possible, appending provided text separated by given separator (default \\n).
	If the message cannot be edited, reply to it instead.
	If text is longer than 4096 characters, message will be split in subsequent replies.
	Accepts any arg that you would pass to message.edit() or message.reply()"""
	if len(text.strip()) == 0:
		return message

	if is_me(message):
		opts = {}
		if "parse_mode" in kwargs: # needed to properly get previous message text
			opts['parse_mode'] = kwargs['parse_mode']
		text = get_text(message, **opts) + separator + text

	fragments = batchify(text, 4096)
	ret : Message

	if is_me(message): # If I sent this message, edit it with the first fragment
		ret = await message.edit(fragments.pop(0), *args, **kwargs)

	for frag in fragments:
		if nomentions: # Edit the message so that it won't mention anyone
			ret = await message.reply("[placeholder]", *args, **kwargs)
			ret = await ret.edit(frag, *args, **kwargs)
		else:
			ret = await message.reply(frag, *args, **kwargs)
	return ret

async def send_media(client:Client, chat_id:int, fname:str, **kwargs):
	"""Will send a media accordingly: with proper method and with right chat_action.
	Will accept any arg that is valid for client.send_photo/video/sticker/voice/document.
	"caption" will be removed from kwargs if sending a sticker or an audio."""
	if fname.endswith((".jpg", ".jpeg", ".png")):
		prog = ProgressChatAction(client, chat_id, action=ChatAction.UPLOAD_PHOTO)
		await client.send_photo(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".gif", ".mp4", ".webm")):
		prog = ProgressChatAction(client, chat_id, action=ChatAction.UPLOAD_VIDEO)
		await client.send_video(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".webp", ".tgs")):
		prog = ProgressChatAction(client, chat_id, action=ChatAction.CHOOSE_STICKER)
		kwargs.pop("caption") # would raise an exception, remove it so it's safe to use from send_media
		await client.send_sticker(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".mp3", ".ogg", ".wav")):
		prog = ProgressChatAction(client, chat_id, action=ChatAction.UPLOAD_AUDIO)
		kwargs.pop("caption") # would raise an exception, remove it so it's safe to use from send_media
		await client.send_voice(chat_id, fname, progress=prog.tick, **kwargs)
	else:
		prog = ProgressChatAction(client, chat_id, action=ChatAction.UPLOAD_DOCUMENT)
		await client.send_document(chat_id, fname, progress=prog.tick, **kwargs)
	await client.send_chat_action(chat_id, ChatAction.CANCEL)
