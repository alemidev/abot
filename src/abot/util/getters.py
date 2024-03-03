from typing import Union

from pyrogram.types import Message, InlineQuery, Chat, User
from pyrogram.enums import ParseMode

def get_text(msg:Union[Message, InlineQuery], raw:bool = False, parse_mode:ParseMode=ParseMode.HTML) -> str:
	if isinstance(msg, Message) and msg.text:
		if not raw:
			if parse_mode == ParseMode.HTML and hasattr(msg.text, "html"):
				return msg.text.html
			if parse_mode == ParseMode.MARKDOWN and hasattr(msg.text, "markdown"):
				return msg.text.markdown
		return msg.text
	if isinstance(msg, Message) and msg.caption:
		if not raw:
			if parse_mode == ParseMode.HTML and msg.caption.html:
				return msg.caption.html
			if parse_mode == ParseMode.MARKDOWN and msg.caption.markdown:
				return msg.caption.markdown
		return msg.caption
	if isinstance(msg, InlineQuery) and msg.query:
		return msg.query
	return ""

def get_user(msg:Message):
	if hasattr(msg, "from_user") and msg.from_user:
		return msg.from_user
	if hasattr(msg, "sender_chat") and msg.sender_chat:
		return msg.sender_chat
	return None

def get_username(entity:Union[Chat, User], mention=True, log=False):
	"""Get username of chat or user. If no username is available, will return
	   user first_name (+last_name if present) or chat title. If mention is True and target
	   is mentionable, a mention will be returned (either with @ or with a tg deeplink).
	   If log is True, the user_id will be included."""
	if not entity:
		return "[Anonymous]"
	if hasattr(entity, 'username') and entity.username:
		if mention:
			if log:
				return f"{entity.id}|@{entity.username}"
			if hasattr(entity, 'title') and entity.title:
				return f"<a href=https://t.me/{entity.username}>{entity.title}</a>"
			return f"@{entity.username}"
		if log:
			return f"{entity.id}|{entity.username}"
		return entity.username
	if mention and not log and hasattr(entity, 'mention') and entity.mention:
		return entity.mention
	if hasattr(entity, 'first_name') and entity.first_name:
		if hasattr(entity, 'last_name') and entity.last_name:
			if log:
				return f"{entity.id}|{entity.first_name} {entity.last_name}"
			return f"{entity.first_name} {entity.last_name}"
		if log:
			return f"{entity.id}|{entity.first_name}"
		return entity.first_name
	if hasattr(entity, 'title') and entity.title:
		if log:
			return f"{entity.id}|{entity.title}"
		if mention and hasattr(entity, 'invite_link') and entity.invite_link:
			return f"<a href={entity.invite_link}>{entity.title}</a>"
		return entity.title
	return str(entity.id)

def get_channel(chat:Chat):
	if chat.title is None:
		return get_username(chat)
	else:
		return chat.title
