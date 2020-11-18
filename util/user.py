def get_username(user):
    if user is None:
        return "N/A"
    elif user.username is None:
        if user.last_name is None:
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
