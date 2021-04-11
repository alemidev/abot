from pyrogram import filters
from pyrogram.filters import create

import json

ALLOWED = {}
SUPERUSER = []

try:
	with open("data/perms.json") as f:
		tmp = json.load(f)
		ALLOWED = { int(k) : v for (k, v) in tmp.items() if k.isnumeric() } # Convert json keys to integers
		SUPERUSER = list(tmp["SUPERUSER"])
except FileNotFoundError:
	with open("data/perms.json", "w") as f:
		json.dump({ "SUPERUSER" : [] }, f)
except KeyError:
	if "SUPERUSER" not in ALLOWED:
		ALLOWED["SUPERUSER"] = []
	with open("data/perms.json", "w") as f:
		json.dump(ALLOWED, f)

def check_superuser(_, __, m): # basically filters.me plus lookup in a list
	return bool(m.from_user and (m.from_user.is_self or m.from_user.id in SUPERUSER) or m.outgoing)

is_superuser = create(check_superuser)

def check_allowed(_, __, m):
	return bool(m.from_user and (m.from_user.id in ALLOWED or check_superuser(None, None, m)) or m.outgoing)

is_allowed = filters.create(check_allowed)

def list_allowed():
	return list(ALLOWED.keys())

def allow(uid, val=True):
	if uid in ALLOWED and ALLOWED[uid] == val:
		return False
	ALLOWED[uid] = val # this is handy when editing manually the file
	serialize()
	return True

def disallow(uid, val=False):
	if uid not in ALLOWED:
		return False
	ALLOWED.pop(uid, None)
	serialize()
	return True

def serialize():
	with open("data/perms.json", "w") as f:
		json.dump(ALLOWED, f)
