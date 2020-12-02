import traceback
import json
import functools

from bot import alemiBot

from pyrogram import filters

from util.permission import is_allowed
from util.message import edit_or_reply, is_me
from util.command import filterCommand

import logging
logger = logging.getLogger(__name__)

CATEGORIES = {}
ALIASES = {}

class HelpEntry:
    def __init__(self, title, shorttext, longtext, public=False, args=""):
        self.shorttext = shorttext
        self.longtext = longtext
        self.args = args
        if isinstance(title, list):
            self.title = title[0]
            for a in title[1:]:
                ALIASES[a] = title[0]
        else:
            self.title = title
        if public:
            self.shorttext += " *"

class HelpCategory: 
    def __init__(self, title):
        self.title = title.upper()
        self.HELP_ENTRIES = {}
        CATEGORIES[self.title] = self

    # TODO maybe redo as decorator
    def add_help(self, title, shorttext, longtext, public=False, args=""):
        h = HelpEntry(title, shorttext, longtext, public=public, args=args)
        self.HELP_ENTRIES[h.title] = h

def get_all_short_text():
    out = ""
    for k in CATEGORIES:
        out += f"`━━┫ {k}`\n"
        cat = CATEGORIES[k]
        for cmd in cat.HELP_ENTRIES:
            entry = cat.HELP_ENTRIES[cmd]
            out += f"`→ .{entry.title} ` {entry.shorttext}\n"
    return out

# The help command
@alemiBot.on_message(is_allowed & filterCommand(["help", "h"], list(alemiBot.prefixes)))
async def help_cmd(client, message):
    logger.info("Help!")
    if len(message.command) > 1:
        for k in CATEGORIES:
            cat = CATEGORIES[k]
            if message.command[1] in cat.HELP_ENTRIES:
                e = cat.HELP_ENTRIES[message.command[1]]
                return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown")
            elif message.command[1] in ALIASES and ALIASES[message.command[1]] in cat.HELP_ENTRIES:
                e = cat.HELP_ENTRIES[ALIASES[message.command[1]]]
                return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown")
    await edit_or_reply(message, f"`ᚨᛚᛖᛗᛁᛒᛟᛏ v{client.app_version}`\n" +
                        "`→ .help [cmd] ` get help, give cmd for specific help\n" +
                        get_all_short_text() +
                        f"__Commands with * are available to trusted users__\n" +
                        "\nhttps://github.com/alemigliardi/alemibot", parse_mode="markdown")
    await client.set_offline()
