from pyrogram.types import Message

def get_text(msg:Message, raw:bool = False, html:bool = False):
	if hasattr(msg, "text") and msg.text:
		if not raw:
			if html and hasattr(msg.text, "html"):
				return msg.text.html
			if not html and hasattr(msg.text, "markdown"):
				return msg.text.markdown
		return msg.text
	if hasattr(msg, "caption") and msg.caption:
		if not raw:
			if html and hasattr(msg.caption, "html"):
				return msg.caption.html
			if not html and hasattr(msg.caption, "markdown"):
				return msg.caption.markdown
		return msg.caption
	if hasattr(msg, "query") and msg.query:
		if not raw:
			if html and hasattr(msg.query, "html"):
				return msg.query.html
			if not html and hasattr(msg.query, "markdown"):
				return msg.query.markdown
		return msg.query
	if raw:
		return None
	return ""

def get_user(msg:Message):
	if hasattr(msg, "from_user") and msg.from_user:
		return msg.from_user
	if hasattr(msg, "sender_chat") and msg.sender_chat:
		return msg.sender_chat
	return None

def get_username(entity, mention=True, log=False):
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
		return entity.title
	return str(entity.id)

def get_channel(chat):
	if chat.title is None:
		return get_username(chat)
	else:
		return chat.title
