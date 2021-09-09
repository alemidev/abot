import re
import json
import asyncio
import logging
import functools
from random import choice

from typing import Union, Optional, List

from time import time

from pyrogram.raw.functions.messages import DeleteScheduledMessages
from pyrogram.raw.functions.messages import Search
from pyrogram.raw.types.messages import MessagesSlice
from pyrogram.raw.types import InputMessagesFilterEmpty
from pyrogram.types import Message
from pyrogram import Client
from pyrogram.errors import ChatWriteForbidden, FloodWait

from . import batchify
from .getters import get_text

def _catch_errors(fun):
	@functools.wraps(fun)
	async def wrapper(*args, **kwargs):
		try:
			await fun(args, kwargs)
		except FloodWait as e:
			logging.error("FloodWait too long (%d s), aborting", e.x)
		except ChatWriteForbidden as e:
			logging.error("Cannot write in this chat")
		except Exception as e:
			logging.exception("ignoring exception in '%s'", fun.__name__)
	return wrapper

class ProgressChatAction:
	"""Helper class for ongoing chat actions.
	Wraps information needed to send the chat action and provides either
	the ability to run the task in background and stop it when done, or to call
	a method which will not send another chat action until cooldown expired.
	Can be used as context manager.
	"""
	ACTIONS = [
		"typing", "upload_photo", "record_video", "upload_video",
		"record_audio", "upload_audio", "upload_document", "find_location",
		"record_video_note", "upload_video_note", "choose_contact",
		"playing", "speaking", "cancel"
	]
	def __init__(
			self,
			client:Client,
			chat_id:int,
			action:str="upload_document",
			random:bool=False,
			interval:float=4.75
	):
		self.client = client
		self.chat_id = chat_id
		self.action = action
		if random:
			self.action = choice(list(set(self.ACTIONS) - {"speaking", "cancel"}))
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
			await self.client.send_chat_action(self.chat_id, self.action)
			self.last = time()

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
	return message.outgoing or (message.from_user is not None 
		and message.from_user.is_self and message.via_bot is None) # can't edit messages from inline bots

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
			opts = {"raw": bool(kwargs["parse_mode"] is None), "html": bool(kwargs["parse_mode"] == "html")}
		text = get_text(message, **opts) + separator + text

	fragments = batchify(text, 4096)
	ret = None

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
		prog = ProgressChatAction(client, chat_id, action="upload_photo")
		await client.send_photo(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".gif", ".mp4", ".webm")):
		prog = ProgressChatAction(client, chat_id, action="upload_video")
		await client.send_video(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".webp", ".tgs")):
		prog = ProgressChatAction(client, chat_id, action="upload_photo")
		kwargs.pop("caption") # would raise an exception, remove it so it's safe to use from send_media
		await client.send_sticker(chat_id, fname, progress=prog.tick, **kwargs)
	elif fname.endswith((".mp3", ".ogg", ".wav")):
		prog = ProgressChatAction(client, chat_id, action="upload_audio")
		kwargs.pop("caption") # would raise an exception, remove it so it's safe to use from send_media
		await client.send_voice(chat_id, fname, progress=prog.tick, **kwargs)
	else:
		prog = ProgressChatAction(client, chat_id, action="upload_document")
		await client.send_document(chat_id, fname, progress=prog.tick, **kwargs)
	await client.send_chat_action(chat_id, "cancel")

def parse_media_type(msg:Message) -> Optional[str]:
	media_types = [
		"voice", "audio", "photo", "dice", "sticker", "animation", "game",
		"video_note", "video", "contact", "location", "venue", "poll", "document",
	]
	for t in media_types:
		if hasattr(msg, t) and getattr(msg, t):
			return t
	return None

def parse_sys_dict(msg):
	events = []
	if "new_chat_members" in msg:
		events.append("new chat members")
	if "left_chat_member" in msg:
		events.append("member left")
	if "new_chat_title" in msg:
		events.append("chat title changed")
	if "new_chat_photo" in msg:
		events.append("chat photo changed")
	if "delete_chat_photo" in msg:
		events.append("chat photo deleted")
	if "group_chat_created" in msg:
		events.append("group chat created")
	if "supergroup_chat_created" in msg:
		events.append("supergroup created")
	if "channel_chat_created" in msg:
		events.append("channel created")
	if "migrate_to_chat_id" in msg:
		events.append("migrate to chat id")
	if "migrate_from_chat_id" in msg:
		events.append("migrate from chat id")
	if "pinned_message" in msg:
		events.append("pinned msg")
	if "game_score" in msg:
		events.append("game score")
	return "SYS[ " + " | ".join(events) + " ]"

async def edit_scheduled(client:Client, message:Message, text:str, *args, **kwargs): # Not really possible, we just delete and resend
	if message.reply_to_message:
		kwargs["reply_to_message_id"] = message.reply_to_message.message_id
	peer = await client.resolve_peer(message.chat.id)
	await client.send(DeleteScheduledMessages(peer=peer, id=[message.message_id]))
	return await client.send_message(message.chat.id, message.text.markdown + "\n" + text, *args,
										 schedule_date=message.date, **kwargs)

async def count_messages(client:Client, chat:int, user:int, offset:int=0, query:str="") -> int:
	messages : MessagesSlice = await client.send(
				Search(
					peer=await client.resolve_peer(chat),
					from_id=await client.resolve_peer(user),
					add_offset=offset,
					filter=InputMessagesFilterEmpty(),
					q=query,
					min_date=0,
					max_date=0,
					offset_id=0,
					limit=0,
					max_id=0,
					min_id=0,
					hash=0,
				)
			)
	return messages.count

async def edit_restart_message(client:Client):
	try:
		with open("data/lastmsg.json", "r") as f:
			lastmsg = json.load(f)
		if "chat_id" in lastmsg and "message_id" in lastmsg:
			message = await client.get_messages(lastmsg["chat_id"], lastmsg["message_id"])
			await message.edit(message.text.markdown + " [`OK`]")
			with open("data/lastmsg.json", "w") as f:
				json.dump({}, f)
	except:
		logging.exception("Error editing restart message")
