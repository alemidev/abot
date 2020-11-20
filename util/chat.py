from util.user import get_username, get_username_dict

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
