from typing import Callable

import pyrogram

CATEGORIES = {}
ALIASES = {}

def ugly_type_check(obj, string):
	return obj.__class__.__name__ in string

def search_filter_command(flt):
	if ugly_type_check(flt, 'CommandFilter'):
		return flt
	if ugly_type_check(flt, ['AndFilter', 'OrFilter']):
		return search_filter_command(flt.base) or search_filter_command(flt.other)
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
		CATEGORIES[self.title] = self

	def add_help(self, title, shorttext, longtext, public=False, args=""):
		print(f"[{public}] {title} - {shorttext} | {args}\n{longtext}")
		h = HelpEntry(title, shorttext, longtext, public=public, args=args)
		self.HELP_ENTRIES[h.title] = h

	def add(self, shorttext:str, cmd=False, public=False):
		def decorator(func: Callable) -> Callable:
			tit = ""
			short = shorttext if shorttext else ""
			long = func.__doc__

			flt = search_filter_command(func.handler[0].filters)
			if flt:
				arg = ""
				tit = list(flt.commands)
				for k in flt.options:
					arg += f"[{flt.options[k][0]} <{k}>] "
				for f in flt.flags:
					arg += f"[{f}] "
			if cmd:
				arg += " [<cmd>]"
			self.add_help(tit, short, long, public, arg)
			return func
		return decorator

def get_all_short_text(pref, sudo=False):
	out = ""
	for k in CATEGORIES:
		out += f"`━━┫ {k}`\n"
		cat = CATEGORIES[k]
		for cmd in cat.HELP_ENTRIES:
			entry = cat.HELP_ENTRIES[cmd]
			if not sudo and not entry.public:
				continue
			out += f"`→ {pref}{entry.title} ` {entry.shorttext}\n"
	return out
