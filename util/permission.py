import os
import json

from typing import Dict, List, Set

from pyrogram import filters
from pyrogram.filters import Filter, create

from bot import alemiBot

import logging
logger = logging.getLogger(__name__)

def check_superuser(update):
	if hasattr(update, "from_user") and update.from_user:
		return update.from_user.is_self or update.from_user.id in alemiBot.sudoers
	elif hasattr(update, "sender_chat") and update.sender_chat:
		return update.sender_chat.id in alemiBot.sudoers
	logger.warning("Received entity with no sender \n\t%s", str(update).replace('\n', '\n\t'))
	return False

sudo = create(lambda _, __, upd : check_superuser(upd))
is_superuser = sudo # backwards compatibility

class JsonDriver:
	def __init__(self, fname:str):
		self.fname = fname
		self.data : Dict[str,List[int]] = {}
		try:
			with open(self.fname) as f:
				self.data = json.load(f)
		except FileNotFoundError:
			self.data = {}
			with open(self.fname, "w") as f:
				json.dump({}, f)
			os.chmod(self.fname, 0o600)

	def _serialize(self):
		with open(self.fname, "w") as f:
			json.dump(self.data, f)

	def put(self, uid:int, group:str = "_") -> bool:
		if group not in self.data:
			self.data[group] = []
		if uid in self.data[group]:
			return False
		self.data[group].append(uid)
		self._serialize()
		return True

	def pop(self, uid:int, group:str = "_") -> bool:
		if group not in self.data:
			return False
		if uid not in self.data[group]:
			return False
		self.data[group].remove(uid)
		self._serialize()
		return True
	
	def any(self, uid:int) -> bool:
		return any(uid in self.data[k] for k in self.data)

	def check(self, uid:int, group:str = "_") -> bool:
		if group not in self.data:
			return False
		return uid in self.data[group]

	def all(self) -> Set[int]:
		return set(uid for grp in self.data for uid in self.data[grp])

PERMS_DB = JsonDriver("data/perms.json")

class PermsFilter(Filter):
	def __init__(self, group:str = "_"):
		self.group = group

	async def __call__(self, client: "pyrogram.Client", update: "pyrogram.types.Update"):
		if is_superuser(client, update) or (self.group == "_" and alemiBot.everyone_allowed):
			return True
		if hasattr(update, "from_user") and update.from_user:
			return PERMS_DB.check(update.from_user.id, self.group)
		elif hasattr(update, "sender_chat") and update.sender_chat:
			return PERMS_DB.check(update.sender_chat.id, self.group)
		raise NotImplementedError

is_allowed = PermsFilter() # backwards compatibility

def check_allowed(msg): # backwards compatibility
	return is_allowed(None, msg)

def list_allowed(): # backwards compatibility
	return list(PERMS_DB.all())

def allow(uid, group="_"): # backwards compatibility
	return PERMS_DB.put(uid, group)

def disallow(uid, group="_"): # backwards compatibility
	return PERMS_DB.pop(uid, group)

