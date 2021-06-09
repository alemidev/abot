import re
import json
import logging

from time import time

from pyrogram.raw.functions.messages import DeleteScheduledMessages
from pyrogram.raw.functions.messages import Search
from pyrogram.raw.types import InputMessagesFilterEmpty, Message
from pyrogram import Client

from . import batchify
from .getters import get_text

class ProgressChatAction:
	def __init__(self, client:Client, chat_id:int, action:str="upload_document", interval:float=4.75):
		self.client = client
		self.chat_id = chat_id
		self.action = action
		self.interval = interval
		self.last = 0

	async def tick(self, *args, **kwargs): # so this can be used as progres callback
		if time() - self.last > self.interval:
			await self.client.send_chat_action(self.chat_id, self.action)
			self.last = time()


def is_me(message):
	return message.outgoing or (message.from_user is not None 
		and message.from_user.is_self and message.via_bot is None) # can't edit messages from inline bots

async def edit_or_reply(message, text, separator="\n", *args, **kwargs):
	if len(text.strip()) == 0:
		return message
	opts = {}
	if "parse_mode" in kwargs: # needed to properly get previous message text
		opts = {"raw": bool(kwargs["parse_mode"] is None), "html": bool(kwargs["parse_mode"] == "html")}
	if is_me(message) and len((get_text(message, raw=True) or "") + text) < 4090:
		if message.scheduled:
			return await edit_scheduled(message._client, message, text, *args, **kwargs)
		else:
			return await message.edit(get_text(message, **opts) + separator + text, *args, **kwargs)
	else:
		ret = None
		for m in batchify(text, 4090):
			ret = await message.reply(m, *args, **kwargs)
		return ret

async def send_media(client, chat_id, fname, **kwargs):
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

def parse_media_type(msg:Message):
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

async def edit_scheduled(client, message, text, *args, **kwargs): # Not really possible, we just delete and resend
	if message.reply_to_message:
		kwargs["reply_to_message_id"] = message.reply_to_message.message_id
	peer = await client.resolve_peer(message.chat.id)
	await client.send(DeleteScheduledMessages(peer=peer, id=[message.message_id]))
	return await client.send_message(message.chat.id, message.text.markdown + "\n" + text, *args,
										 schedule_date=message.date, **kwargs)

async def count_messages(client, chat, user, offset=0, query=""):
	messages = await client.send(
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

async def edit_restart_message(client):
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