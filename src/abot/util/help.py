from typing import Callable

import pyrogram
from pyrogram.filters import AndFilter, OrFilter, InvertFilter

CATEGORIES = {}
ALIASES = {}

def search_filter_command(flt):
	if hasattr(flt, "commands") and hasattr(flt, "options") and hasattr(flt, "flags"):
		return flt # Since all CommandFilters are made with filters.create, they all have different classes! Can't isinstance them
	if isinstance(flt, (AndFilter, OrFilter)):
		return search_filter_command(flt.base) or search_filter_command(flt.other)
	if isinstance(flt, InvertFilter):
		return search_filter_command(flt.base)
	return None

class HelpEntry:
	def __init__(self, title, shorttext, longtext, public=False, args=""):
		self.shorttext = shorttext
		self.longtext = longtext
		self.args = args
		self.public = public
		if isinstance(title, list):
			self.title = title[0]
			for a in title[1:]:
				ALIASES[a] = title[0]
		else:
			self.title = title

class HelpCategory: 
	def __init__(self, title):
		self.title = title.upper()
		self.HELP_ENTRIES = {}
		CATEGORIES[self.title.upper()] = self

	def add_help(self, title, shorttext, longtext, public=False, args=""):
		h = HelpEntry(title, shorttext, longtext, public=public, args=args)
		self.HELP_ENTRIES[h.title] = h

	def add(self,
			title:str = "",
			shorttext:str = "",
			longtext:str = "",
			cmd:str = "",
			sudo:bool = True,
		) -> Callable:
		"""This decorator (factory) adds a help entry fetching title, aliases, args and
		longtext from the filterCommand and the function docstring. It's kind of a botchy
		method but I didn't want to overload pyrogram client decorators. This will only work
		inside smart plugins thanks to pyrogram botch: it will check the handler in the function
		itself and dig in its filters to find a filterCommand, and get values from that.
		Add cmd=True to append a '[<cmd>]' at the end of the arglist. Put sudo=False to make the
		command available to trusted users."""
		def decorator(func: Callable) -> Callable:
			name = title
			short = shorttext
			long = longtext
			args = ""
			if hasattr(func, "handlers"):
				for handler, group in func.handlers:
					flt = search_filter_command(handler.filters)
					if not flt:
						continue
					name = list(flt.commands)
					for k in flt.options:
						args += f"[{flt.options[k][0]} <{k}>] "
					for f in flt.flags:
						args += f"[{f}] "
					break
			if cmd:
				args += cmd
			if func.__doc__:
				short = func.__doc__.split("\n")[0]
				long = func.__doc__
			self.add_help(name, short, long, not sudo, args)
			return func
		return decorator

def get_all_short_text(pref, sudo=False):
	out = ""
	for k in CATEGORIES:
		out += f"<code>━━┫ {k}</code>\n"
		cat = CATEGORIES[k]
		for cmd in cat.HELP_ENTRIES:
			entry = cat.HELP_ENTRIES[cmd]
			if not sudo and not entry.public:
				continue
			out += f"→ <code>{pref}{entry.title}</code> {entry.shorttext}\n"
	return out
