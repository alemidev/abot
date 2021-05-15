import os
import json

from typing import Dict, List, Set

from pyrogram import filters
from pyrogram.filters import Filter, create

from bot import alemiBot

import logging
logger = logging.getLogger(__name__)

class JsonDriver:
	def __init__(self, fname:str):
		self.fname = fname
		self.data : Dict[str,List[int]] = {}
		try:
			with open(self.fname) as f:
				self.data = { k:set(v) for k,v in json.load(f) }
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

class SudoFilter(Filter):
	SUPERUSER = [ int(k.strip()) for k in
					alemiBot.config.get("perms", "sudo", fallback="").split()
				]
	async def __call__(self, client: "pyrogram.Client", update: "pyrogram.types.Update"):
		if hasattr(update, "from_user") and update.from_user:
			return update.from_user.is_self or update.from_user.id in self.SUPERUSER
		elif hasattr(update, "sender_chat") and update.sender_chat:
			return update.sender_chat.id in self.SUPERUSER
		raise NotImplementedError

is_superuser = SudoFilter()

class PermsFilter(Filter):
	def __init__(self, group:str = ""):
		self.group = group

	async def __call__(self, client: "pyrogram.Client", update: "pyrogram.types.Update"):
		if is_superuser(client, update):
			return True
		if hasattr(update, "from_user") and update.from_user:
			return PERMS_DB.check(update.from_user.id, self.group)
		elif hasattr(update, "sender_chat") and update.sender_chat:
			return PERMS_DB.check(update.sender_chat.id, self.group)
		raise NotImplementedError

is_allowed = PermsFilter()

def list_allowed():
	return list(PERMS_DB.all())

def allow(uid, group="_"):
	return PERMS_DB.put(uid, group)

def disallow(uid, group="_"):
	return PERMS_DB.pop(uid, group)

