import traceback
import json

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from util.message import is_me, get_text
from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

HELP = HelpCategory("TRIGGER")

triggers = {}
try:
    with open("data/triggers.json") as f:
        triggers = json.load(f)
except:
    pass

HELP.add_help(["trigger", "trig"], "register a new trigger",
            "Add a new trigger sequence and corresponding message. Use " +
            "sigle quotes `'` to wrap triggers with spaces (no need to wrap message). " +
            "Use this command to list triggers (`-l`), add new (`-n`) and delete (`-d`). " +
            "Triggers will always work in private chats, but only work when mentioned in groups." ,
            args="( -l | -d <trigger> | -n <trigger> <message> )")
@alemiBot.on_message(filters.me & filters.command(["trigger","trig"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:trigger|trig)(?: |)(?P<arg>-l|-n|-d)(?: |)(?P<trigger>'.+'|[^ ]+|)(?: |)(?P<message>.+|)"
))
async def trigger_cmd(client, message):
    args = message.matches[0]
    changed = False
    if args["arg"] == "-l":
        logger.info("Listing triggers")
        out = "\n"
        for t in triggers:
            out += f"`'{t}' → ` {triggers[t]}\n"
        if out == "\n":
            out += "` → Nothing to display`"
        await message.edit(message.text.markdown + out)
    elif args["arg"] == "-n" and args["trigger"] != "" and args["message"] != "":
        logger.info("New trigger")
        triggers[args["trigger"].strip("'")] = args["message"]
        await message.edit(message.text.markdown + f"\n` → ` Registered new trigger")
        changed = True
    elif args["arg"] == "-d" and args["trigger"] != "":
        logger.info("Removing trigger")
        if triggers.pop(args["trigger"].strip("'"), None) is not None:
            await message.edit(message.text.markdown + "\n` → ` Removed trigger")
            changed = True
    else:
        return await message.edit(message.text.markdown + "\n`[!] → ` Wrong use")
    if changed:
        with open("data/triggers.json", "w") as f:
            json.dump(triggers, f)

@alemiBot.on_message(group=8)
async def search_triggers(client, message):
    if is_me(message) or message.edit_date is not None:
        return # pyrogram gets edit events as message events!
    if message.chat is None:
        return # wtf messages with no chat???
    if message.chat.type != "private" and not message.mentioned:
        return # in groups only get triggered in mentions
    msg_txt = get_text(message).lower()
    if msg_txt == "":
        return
    for trg in triggers:
        if trg.lower() in msg_txt:
            await message.reply(triggers[trg])
            await client.set_offline()
            logger.info("T R I G G E R E D")
