from pyrogram.types import Message

def get_text(msg:Message, raw=False):
	if hasattr(msg, "text"):
		if raw and hasattr(msg.text, "raw"):
			return msg.text.raw
		elif hasattr(msg.text, "markdown"):
			return msg.text.markdown
		return msg.text
	elif hasattr(msg, "caption"):
		return msg.caption
	if raw:
		return None
	else:
		return ""

def get_text_dict(message):
	if "text" in message:
		return message["text"]
	elif "caption" in message:
		return message["caption"]
	else:
		return {"markdown": "", "raw": ""}

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

def get_username_dict(user):
	if user is None:
		return "UNKNOWN"
	elif "username" in user:
		return "@" + user['username']
	else:
		if "last_name" in user:
			return user['first_name'] + ' ' + user['last_name']
		else:
			return user['first_name']

def get_channel(chat):
	if chat.title is None:
		return get_username(chat)
	else:
		return chat.title

def get_channel_dict(chat):
	if "title" not in chat:
		return get_username_dict(chat)
	else:
		return chat["title"]