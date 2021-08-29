import json

from typing import Any, Dict, Optional

class Context:
	def __init__(self):
		super().__setattr__('_store', {}) # must be done like this since I overload __setattr__

	def __str__(self) -> str:
		return json.dumps(self._store, indent=2, default=str)

	def __repr__(self) -> str:
		return json.dumps(self._store, default=str)

	def __hash__(self) -> int:
		return hash(self._store)

	def __bool__(self) -> bool:
		return bool(self._store)

	def __getitem__(self, name:str) -> Optional[Any]:
		if name not in self._store:
			return None
		return self._store[name]

	def __setitem__(self, name:str, value:Any):
		self._store[name] = value

	def __getattr__(self, name:str) -> Any:
		return self.__getitem__(name)

	def __setattr__(self, name:str, value:Any):
		return self.__setitem__(name, value)
