import traceback
import json

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed, is_superuser
from util.message import is_me, get_text, edit_or_reply
from util.command import filterCommand
from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

HELP = HelpCategory("TRIGGER")

TRIGGERS = {}
try:
    with open("data/triggers.json") as f:
        buf = json.load(f)
        for k in buf:
            TRIGGERS[k] = { "pattern" : re.compile(k), "reply" : buf[k] }
except:
    pass

def serialize():
    global TRIGGERS
    with open("data/triggers.json", "w") as f:
        json.dump({ key : TRIGGERS[key]["reply"] for key in TRIGGERS }, f)

HELP.add_help(["trigger", "trig"], "register a new trigger",
            "Add a new trigger sequence and corresponding message. Regex can be used. Use " +
            "sigle quotes `'` to wrap triggers with spaces (no need to wrap message). " +
            "Use this command to list triggers (`-list`), add new (`-n`) and delete (`-d`). " +
            "Triggers will always work in private chats, but only work when mentioned in groups." ,
            args="( -list | -d <trigger> | -n <trigger> <message> )")
@alemiBot.on_message(is_superuser & filterCommand(["trigger", "trig"], list(alemiBot.prefixes), options={
    "new" : ["-n", "-new"],
    "del" : ["-d", "-del"]
}, flags=["-list"]))
async def trigger_cmd(client, message):
    global TRIGGERS
    args = message.command

    changed = False
    if "-list" in args["flags"]:
        logger.info("Listing triggers")
        out = ""
        for t in TRIGGERS:
            out += f"`{TRIGGERS[t]['pattern'].pattern} → ` {TRIGGERS[t]['reply']}\n"
        if out == "":
            out += "` → Nothing to display`"
        await edit_or_reply(message, out)
    elif "new" in args and "arg" in args:
        logger.info("New trigger")
        pattern = re.compile(args["new"])
        TRIGGERS[args["new"]] = { "pattern": pattern, "reply" : args["arg"] }
        await edit_or_reply(message, f"` → ` New trigger `{pattern.pattern}`")
        changed = True
    elif "del" in args:
        logger.info("Removing trigger")
        if TRIGGERS.pop(args["del"], None) is not None:
            await edit_or_reply(message, "` → ` Removed trigger")
            changed = True
    else:
        return await edit_or_reply(message, "`[!] → ` Wrong use")
    if changed:
        serialize()

@alemiBot.on_message(group=8)
async def search_triggers(client, message):
    global TRIGGERS
    if is_me(message) or message.edit_date is not None: # TODO allow triggers for self?
        return # pyrogram gets edit events as message events!
    if message.chat is None:
        return # wtf messages with no chat???
    if message.chat.type != "private" and not message.mentioned:
        return # in groups only get triggered in mentions
    msg_txt = get_text(message).lower()
    if msg_txt == "":
        return
    for key in TRIGGERS:
        if TRIGGERS[key]["pattern"].search(message.text):
            await message.reply(TRIGGERS[key]["reply"])
            await client.set_offline()
            logger.info("T R I G G E R E D")
