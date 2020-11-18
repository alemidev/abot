from pyrogram import filters

import json

ALLOWED = {}

with open("data/perms.json") as f:
    ALLOWED = json.load(f)

def check_allowed(_, __, message):
    if message.from_user is None:
        return False
    return str(message.from_user.id) in ALLOWED

is_allowed = filters.create(check_allowed)

def list_allowed():
    return list(ALLOWED.keys())

def allow(uid, val=True):
    if uid in ALLOWED and ALLOWED[uid] == val:
        return False
    ALLOWED[str(uid)] = val # this is handy when editing manually the file
    serialize()
    return True

def disallow(uid):
    if str(uid) not in ALLOWED:
        return False
    ALLOWED.pop(str(uid), None)
    serialize()
    return True

def serialize():
    with open("data/perms.json", "w") as f:
        json.dump(ALLOWED, f)
