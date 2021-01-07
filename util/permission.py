from pyrogram import filters
from pyrogram.filters import create

import json

ALLOWED = {}
SUPERUSER = []

try:
    with open("data/perms.json") as f:
        ALLOWED = json.load(f)
        SUPERUSER = list(ALLOWED["SUPERUSER"])
except FileNotFoundError:
    with open("data/perms.json", "w") as f:
        json.dump({}, f)
except KeyError:
    ALLOWED["SUPERUSER"] = []
    with open("data/perms.json", "w") as f:
        json.dump(ALLOWED, f)

def check_allowed(_, __, message):
    if message.from_user is None:
        return False
    if message.from_user.is_self:
        return True
    return str(message.from_user.id) in ALLOWED \
            or str(message.from_user.id) in SUPERUSER

is_allowed = filters.create(check_allowed)

async def superuser_filter(_, __, m): # basically filters.me plus lookup in a list
    return bool(m.from_user and (m.from_user.is_self or m.from_user.id in SUPERUSER) or m.outgoing)

is_superuser = create(superuser_filter)

def list_allowed():
    return list(int(k) for k in ALLOWED.keys() if key.isnumeric())

def allow(uid, val=True):
    if str(uid) in ALLOWED and ALLOWED[str(uid)] == val:
        return False
    ALLOWED[str(uid)] = val # this is handy when editing manually the file
    serialize()
    return True

def disallow(uid, val=False):
    if str(uid) not in ALLOWED:
        return False
    ALLOWED.pop(str(uid), None)
    serialize()
    return True

def serialize():
    with open("data/perms.json", "w") as f:
        json.dump(ALLOWED, f)
