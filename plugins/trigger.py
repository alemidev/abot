import traceback
import json

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from util.message import is_me
from plugins.help import HelpCategory

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
            "Use this command to list triggers (`-l`), add new (`-n`) and delete (`-d`).",
            args="( -l | -d <trigger> | -n <trigger> <message> )")
@alemiBot.on_message(filters.me & filters.command(["trigger","trig"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:trigger|trig)(?: |)(?P<arg>-l|-n|-d)(?: |)(?P<trigger>'.+'|[^ ]+|)(?: |)(?P<message>.+|)"
))
async def trigger_cmd(client, message):
    args = message.matches[0]
    changed = False
    if args["arg"] == "-l":
        out = "\n"
        for t in triggers:
            out += f"`'{t}' → ` {triggers[t]}\n"
        if out == "\n":
            out += "` → Nothing to display`"
        await message.edit(message.text.markdown + out)
    elif args["arg"] == "-n" and args["trigger"] != "" and args["message"] != "":
        triggers[args["trigger"].strip("'")] = args["message"]
        await message.edit(message.text.markdown + f"\n` → ` Registered new trigger")
        changed = True
    elif args["arg"] == "-d" and args["trigger"] != "":
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
    for trg in triggers:
        if trg.lower() in message.text.lower():
            await message.reply(triggers[trg])
            await client.set_offline()
