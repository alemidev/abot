"""This is my reimplementation of filter.command

It will parse options ( `-opt value` ), flags ( `-flag` ) and arguments. Matches will
be put in a CommandMatch object for easier access.
"""
import re
import json

from typing import Dict, List, Union, Any
from pyrogram.types import Message
from pyrogram.filters import create

class ConsumableBuffer:
	"""Wrapper for a string which needs tokens replaced"""
	def __init__(self, value:str):
		self.val = value

	def __str__(self):
		return self.val

	def consume(self, token:Union[str,List[str]]):
		"""Replace first occurrance of token in self. Also remove whitespace around"""
		if isinstance(token, list):
			for tok in token:
				self.val = re.sub(rf"(\s|^)('|\"|){re.escape(tok)}(\2)(\s|$)", r"\1", self.val, 1)
		else:
			self.val = re.sub(rf"(\s|^)('|\"|){re.escape(token)}(\2)(\s|$)", r"\1", self.val, 1)

class CommandMatch:
	"""Command match object, will hold any matched flag/option/argument

	You can access command base, text, arg, flags and options directly as attributes
	use hash based access (__getitem__): accessing an int will search in arg and accessing
	a string will search first in flags and then in options. If nothing is available, None
	is returned (so you can do `msg.cmd["opt"] or "default"`). You can test how many arguments
	were passed directly calling `len()` on this object.
	"""
	def __init__(self, base:str):
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

	def __len__(self) -> int:
		return len(self.arg)

	def __contains__(self, name:str):
		return name in self.flags or name in self.options

	def __getitem__(self, key:Union[str,int,slice]):
		if isinstance(key, slice) or ( isinstance(key, int)
				and len(self.arg) > abs(key)):
			return self.arg[key]
		if isinstance(key, str):
			if key in self.flags:
				return True
			if key in self.options:
				return self.options[key]
		return None # no exc, so it can be used with an or

	def option(self, name:str, default:Any = None):
		"""get an option if present, or default value (None if not given)"""
		if name in self.options:
			return self.options[name]
		return default


def filterCommand(commands: Union[str,List[str]], prefixes: Union[str,List[str]] = "/",
			options: Union[Dict[str, List[str]],None] = None, flags: Union[List[str],None] = None, case_sensitive: bool = False):
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
	if not flags:
		flags = []
	if not options:
		options = {}
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
