from pyrogram.types import Message

def get_text(msg:Message, raw:bool=False):
	if hasattr(msg, "text") and msg.text:
		if raw and hasattr(msg.text, "raw"):
			return msg.text.raw
		if not raw and hasattr(msg.text, "markdown"):
			return msg.text.markdown
		return msg.text
	if hasattr(msg, "caption") and msg.caption:
		return msg.caption
	if raw:
		return None
	return ""

def get_user(msg:Message):
	if hasattr(msg, "from_user") and msg.from_user:
		return msg.from_user
	if hasattr(msg, "sender_chat") and msg.sender_chat:
		return msg.sender_chat
	return None

def get_username(entity, mention=True):
	"""Get username of chat or user. If no username is available, will return
	   user first_name (+last_name if present) or chat title. If mention is True
	   and it's a user, will try to mention user with url when no username is available"""
	if not entity:
		return "UNKNOWN"
	if hasattr(entity, 'username') and entity.username:
		if mention:
			return "@" + entity.username
		return entity.username
	if mention and hasattr(entity, 'mention') and entity.mention:
		return entity.mention
	if hasattr(entity, 'first_name') and entity.first_name:
		if hasattr(entity, 'last_name') and entity.last_name:
			return f"{entity.first_name} {entity.last_name}"
		return entity.first_name
	if hasattr(entity, 'title') and entity.title:
		return entity.title
	return "UNKNOWN"

def get_channel(chat):
	if chat.title is None:
		return get_username(chat)
	else:
		return chat.title