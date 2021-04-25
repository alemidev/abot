import json

from pyrogram import filters
from pyrogram.filters import create

import logging
logger = logging.getLogger(__name__)

ALLOWED = {}
SUPERUSER = []

try:
	with open("data/perms.json") as f:
		tmp = json.load(f)
		if "SUPERUSER" in tmp:
			SUPERUSER = list(tmp["SUPERUSER"])
		ALLOWED = { int(k) : v for (k, v) in tmp.items() if k.isnumeric() } # Convert json keys to integers
except FileNotFoundError:
	with open("data/perms.json", "w") as f:
		json.dump({ "SUPERUSER" : [] }, f)
except:
	logger.exception("Error while loading permission file")

def check_superuser(msg): # basically filters.me plus lookup in a list
	return bool(msg.from_user and (msg.from_user.is_self or msg.from_user.id in SUPERUSER) or msg.outgoing)

is_superuser = create(lambda _, __, msg: check_superuser(msg))

def check_allowed(msg):
	return bool(msg.from_user and (msg.from_user.id in ALLOWED or check_superuser(msg)) or msg.outgoing)

is_allowed = filters.create(lambda _, __, msg: check_allowed(msg))

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
