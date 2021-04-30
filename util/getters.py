from pyrogram.types import Message

def get_text(msg:Message, raw:bool=False):
	if hasattr(msg, "text"):
		if raw and hasattr(msg.text, "raw"):
			return msg.text.raw
		elif not raw and hasattr(msg.text, "markdown"):
			return msg.text.markdown
		return msg.text
	elif hasattr(msg, "caption"):
		return msg.caption
	if raw:
		return None
	else:
		return ""

def get_user(msg:Message):
	if hasattr(msg, "from_user") and msg.from_user:
		return msg.from_user
	if hasattr(msg, "sender_chat") and msg.sender_chat:
		return msg.sender_chat
	return None

def get_username(user, mention=False):
	if user is None:
		return "UNKNOWN"
	elif user.username is None:
		if mention:
			return user.mention
		elif user.last_name is None:
			return user.first_name
		else:
			return user.first_name + ' ' + user.last_name
	else:
		return "@" + user.username

def get_channel(chat):
	if chat.title is None:
		return get_username(chat)
	else:
		return chat.title