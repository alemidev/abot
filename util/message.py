import re

from pyrogram.raw.functions.messages import DeleteScheduledMessages
from pyrogram.raw.functions.messages import Search
from pyrogram.raw.types import InputMessagesFilterEmpty, Message

from . import batchify
from .getters import get_text

def is_me(message):
	return message.from_user is not None \
	and message.from_user.is_self \
	and message.via_bot is None # can't edit messages from inline bots

async def edit_or_reply(message, text, *args, **kwargs):
	if len(text.strip()) == 0:
		return message
	if is_me(message) and len(get_text(message) + text) < 4090:
		if message.scheduled: # lmao ye right import more bloat
			await edit_scheduled(message._client, message, text, *args, **kwargs)
		else:
			await message.edit(get_text(message) + "\n" + text, *args, **kwargs)
		return message
	else:
		ret = None
		for m in batchify(text, 4090):
			ret = await message.reply(m, *args, **kwargs)
		return ret

def parse_media_type(msg:Message):
	media_types = [
		"voice", "audio", "photo", "dice", "sticker", "animation", "game",
		"video_note", "video", "contact", "location", "venue", "poll", "document"
	]
	for t in media_types:
		if hasattr(msg, t):
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