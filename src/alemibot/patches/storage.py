import json

from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from pyrogram.storage import Storage, FileStorage

DOCUMENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents
(
	key TEXT PRIMARY KEY,
	doc TEXT
);

CREATE TABLE IF NOT EXISTS last_message
(
	chat_id INTEGER,
	message_id INTEGER
);
"""

class DocumentFileStorage(FileStorage):
	"""
	A wrapper around pyrogram FileStorage to add simple document-like capabilities in json format.
	It's not efficient and more complex use-cases should directly run query on the connection object, but 
	simple values can be made persistant easily. It also by default creates and searches the session object inside 
	the data folder, to not litter top level with runtime data.
	"""
	def __init__(self, name: str, workdir: Path):
		super().__init__(name, workdir / 'data')

	def update(self):
		super().update()
		with self.lock:
			self.conn.executescript(DOCUMENT_SCHEMA)

	def _get_last_message(self) -> Optional[Tuple[int, int]]:
		res = self.conn.execute("SELECT * FROM last_message").fetchone()
		if res:
			self.conn.execute("DELETE FROM last_message")
			return res
		return None

	def _set_last_message(self, chat_id:int, message_id:int):
		self.conn.execute("DELETE FROM last_message")
		self.conn.execute("INSERT INTO last_message VALUES (?, ?)", (chat_id, message_id,))

	def get_doc(self, key:str) -> Dict[str, Any]:
		with self.lock:
			return json.loads(
				self.conn.execute(
					"SELECT doc FROM documents WHERE key = ?", (key,)
				).fetchone()
			)

	def put_doc(self, key:str, doc:Dict[str, Any]) -> None:
		with self.lock:
			self.conn.execute("DELETE FROM documents WHERE key = ?", (key, ))
			self.conn.execute("INSERT INTO documents VALUES (?, ?)", (key, json.dumps(doc), ))

