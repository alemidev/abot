import re
import json

from typing import Dict, List, Union, Any
from pyrogram.types import Message
from pyrogram.filters import create

class ConsumableBuffer:
	def __init__(self, value:str):
		self.val = value

	def __str__(self):
		return self.val

	def get(self):
		return self.val

	def consume(self, token:Union[str,List[str]]):	
		if isinstance(token, list):
			for t in token:
				self.val = re.sub(rf"(\s|^|'|\"){t}(\s|$|'|\")", " ", self.val, 1)
		else:
			self.val = re.sub(rf"(\s|^){token}(\s|$)", r"\1", self.val, 1)

class CommandMatch:
	def __init__(self, base):
		self.base:str = base
		self.text:str = ""
		self.arg:List[str] = []
		self.flags:List[str] = []
		self.options:Dict[str:str] = {}

	def __str__(self) -> str:
		return json.dumps({
			"base" : self.base,
			"text" : self.text,
			"arg" : self.arg,
			"flags" : self.flags,
			"options" : self.options,
			}, indent=2)

	def option(self, name:str, default:Any = None):
		if name in self.options:
			return self.options[name]
		return default

	def get_options(self) -> List[str]:
		return list(self.options.keys())

	def has_option(self, name:str) -> bool:
		return name in self.options

	def __contains__(self, name:str): # Backwards-compatibility, don't use me
		if name == "cmd":
			return bool(self.arg)
		if name in ("args", "raw"):
			return bool(self.text)

	def __getitem__(self, name:str): # Backwards-compatibility, don't use me!
		if name == "flags":
			return self.flags
		if name == "cmd":
			return self.arg
		if name in ("args", "raw"):
			return self.text
		return self.options[name]

def filterCommand(commands: Union[str,List[str]], prefixes: Union[str,List[str]] = "/",
			options: Dict[str, List[str]] = {}, flags: List[str] = [], case_sensitive: bool = False):
	"""Filter commands, i.e.: text messages starting with "/" or any other custom prefix.
	Parameters:
		commands (``str`` | ``list``):
			The command or list of commands as string the filter should look for.
			Examples: "start", ["start", "help", "settings"]. When a message text containing
			a command arrives, the command itself and its arguments will be stored in the *command*
			field of the :obj:`~pyrogram.types.Message`.
		prefixes (``str`` | ``list``, *optional*):
			A prefix or a list of prefixes as string the filter should look for.
			Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
			Pass None or "" (empty string) to allow commands with no prefix at all.
		options (``dict { str : list }``, *optional*):
			A dictionary with name and list of keywords to match. If a keyword is matched 
			in the commands, it will be consumed together with next element and put in the 
			resulting "options" dict for ease of access. Examples : { "time": ["-t"] }
		flags (``list``, *optional*):
			A list of flags to search in the commands. If an element equals a flag given, it 
			will be consumed and put in the resulting "flags" list. Example : [ "-list" ]
		case_sensitive (``bool``, *optional*):
			Pass True if you want your command(s) to be case sensitive. Defaults to False.
			Examples: when True, command="Start" would trigger /Start but not /start.
	"""
	command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

	async def func(flt, client, message: Message):
		if message.scheduled: # allow to trigger commands!
			return False
		text = message.text or message.caption
		message.command = None

		if not text:
			return False

		pattern = r"^{cmd}(?:@{uname}|)(?:\s|$)" if flt.case_sensitive else r"(?i)^{cmd}(?:@{uname}+|)(?:\s|$)"

		for prefix in flt.prefixes:
			if not text.startswith(prefix):
				continue

			without_prefix = text[len(prefix):]
			my_username = client.me.username if hasattr(client, "me") else (await client.get_me()).username

			for cmd in flt.commands:
				if not re.match(pattern.format(cmd=re.escape(cmd), uname=my_username), without_prefix):
					continue

				without_cmd = re.sub("^@[^ ]+", "", without_prefix[len(cmd):])[1:] # remove 1st whitespace
				# match.groups are 1-indexed, group(1) is the quote, group(2) is the text
				# between the quotes, group(3) is unquoted, whitespace-split text

				# Remove the escape character from the arguments
				match_list = [
					re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
					for m in command_re.finditer(without_cmd)
				]
				
				raw_buf = ConsumableBuffer(without_cmd)
				message.command = CommandMatch(cmd)

				while len(match_list) > 0:
					token = match_list.pop(0)
					if token in flt.flags:
						raw_buf.consume(token)
						message.command.flags.append(token)
						continue
					found = False
					for opt in flt.options:
						if token in flt.options[opt]:
							found = True
							val = match_list.pop(0) # pop the value
							raw_buf.consume([token, val])
							message.command.options[opt] = val
							break
					if found:
						continue
					message.command.arg.append(token)

				message.command.text = str(raw_buf).strip()

				return True

		return False

	commands = commands if isinstance(commands, list) else [commands]
	commands = [c if case_sensitive else c.lower() for c in commands]

	prefixes = [] if prefixes is None else prefixes
	prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
	prefixes = set(prefixes) if prefixes else {""}

	flags = flags if isinstance(flags, list) else [flags]

	for k in options:
		options[k] = options[k] if isinstance(options[k], list) else [options[k]]


	return create(
		func,
		"CommandFilter",
		commands=commands,
		prefixes=prefixes,
		case_sensitive=case_sensitive,
		options=options,
		flags=flags
	)
