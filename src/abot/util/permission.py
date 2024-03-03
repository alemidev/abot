import os
import json

from typing import Dict, List, Set, Type

from pyrogram import filters
from pyrogram.filters import Filter, create
from pyrogram.types import Update

import logging
logger = logging.getLogger(__name__)

class AuthStorageDriver:
	name : str
	data : Dict[str,List[int]]

	def __init__(self, name:str):
		self.data = {}
		self.name = name
		self.deserialize()

	def deserialize(self):
		raise NotImplementedError

	def serialize(self):
		raise NotImplementedError


class JsonDriver(AuthStorageDriver):
	fname : str

	def __init__(self, name:str):
		self.fname = f'data/perms-{name}.json'
		super().__init__(name)

	def deserialize(self):
		try:
			with open(self.fname) as f:
				self.data = json.load(f)
		except FileNotFoundError:
			with open(self.fname, "w") as f:
				json.dump({}, f)
			os.chmod(self.fname, 0o600)

	def serialize(self):
		with open(self.fname, "w") as f:
			json.dump(self.data, f)

class Authenticator:
	name : str # The session name
	storage : AuthStorageDriver

	def __init__(self, name:str, driver:Type[AuthStorageDriver] = JsonDriver):
		self.name = name
		self.storage = driver(name)

	def put(self, uid:int, group:str = "_") -> bool:
		if group not in self.storage.data:
			self.storage.data[group] = []
		if uid in self.storage.data[group]:
			return False
		self.storage.data[group].append(uid)
		self.storage.serialize()
		return True

	def pop(self, uid:int, group:str = "_") -> bool:
		if group not in self.storage.data:
			return False
		if uid not in self.storage.data[group]:
			return False
		self.storage.data[group].remove(uid)
		self.storage.serialize()
		return True
	
	def any(self, uid:int) -> bool:
		return any(uid in self.storage.data[k] for k in self.storage.data)

	def check(self, uid:int, group:str = "_") -> bool:
		if group not in self.storage.data:
			return False
		return uid in self.storage.data[group]

	def all(self) -> Set[int]:
		return set(uid for grp in self.storage.data for uid in self.storage.data[grp])

@create
def sudo(flt:Filter, client:'aBot', update:Update):
	if hasattr(update, "from_user") and update.from_user:
		return update.from_user.is_self or update.from_user.id in client.sudoers
	elif hasattr(update, "sender_chat") and update.sender_chat:
		return update.sender_chat.id in client.sudoers
	logger.warning("Received entity with no sender \n\t%s", str(update).replace('\n', '\n\t'))
	return False

# TODO why is one done with filters.create but not the other????

class PermsFilter(Filter):
	def __init__(self, group:str = "_"):
		self.group = group

	async def __call__(self, client: 'aBot', update: Update):
		if sudo(client, update) or (self.group == "_" and client.public):
			return True
		if hasattr(update, "from_user") and update.from_user:
			return client.auth.check(update.from_user.id, self.group)
		elif hasattr(update, "sender_chat") and update.sender_chat:
			return client.auth.check(update.sender_chat.id, self.group)
		raise NotImplementedError

is_allowed = PermsFilter() # backwards compatibility
