from typing import Callable

CATEGORIES = {}
ALIASES = {}

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
		h = HelpEntry(title, shorttext, longtext, public=public, args=args)
		self.HELP_ENTRIES[h.title] = h

	def add(self, title, shorttext, public=False, args=""):
		def decorator(func: Callable) -> Callable:
			longtext = func.__doc__
			self.add_help(title, shorttext, longtext, public, args)
		return decorator

def get_all_short_text(pref, sudo=False):
	out = ""
	for k in CATEGORIES:
		out += f"`━━┫ {k}`\n"
		cat = CATEGORIES[k]
		for cmd in cat.HELP_ENTRIES:
			if not sudo and not cmd.public:
				continue
			entry = cat.HELP_ENTRIES[cmd]
			out += f"`→ {pref}{entry.title} ` {entry.shorttext}\n"
	return out