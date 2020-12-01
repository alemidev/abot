import asyncio
import subprocess
import traceback
import logging
import re
import json

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from util.message import is_me
from util.user import get_username
from util.parse import newFilterCommand

from plugins.help import HelpCategory

logger = logging.getLogger(__name__)

HELP = HelpCategory("BULLY")

censoring = {"MASS": [],
             "FREE": [],
             "SPEC" : {} }
try: # TODO THIS IS BAD MAYBE DON'T USE JSON FFS NICE CODE BRUUH
    with open("data/censoring.json") as f:
        buf = json.load(f)
        for k in buf:
            censoring["SPEC"][int(k)] = buf[k]
        censoring["MASS"] = [ int(e) for e in buf["MASS"] ]
        censoring["FREE"] = [ int(u) for u in buf["FREE"] ]
except FileNotFoundError:
    with open("data/censoring.json", "w") as f:
        json.dump(censoring, f)
except:
    traceback.print_exc()
    # ignore

INTERRUPT = False

HELP.add_help(["censor", "c"], "immediately delete messages from users",
            "Start censoring someone in current chat. Use flag `-mass` to toggle mass censorship in current chat. " +
            "Add flag -free to stop istead stop censoring target. Use flag `-list` to get censored " +
            "users in current chat. Messages from self will never be censored. More than one target can be specified",
            args="[-list] [-i] [-mass] <targets>")
@alemiBot.on_message(filters.me & newFilterCommand(["censor", "c"], list(alemiBot.prefixes), flags=["-list", "-i", "-mass"]))
async def censor_cmd(client, message):
    global censoring
    args = message.command
    out = message.text.markdown + "\n"
    changed = False
    try:
        if "-list" in args["flags"]:
            if message.chat.id not in censoring["SPEC"]:
                out += "` → ` Nothing to display\n"
            else:
                usr_list = await client.get_users(censoring["SPEC"][message.chat.id])
                for u in usr_list:
                    out += "` → ` {get_username(u)}\n"
        elif "-mass" in args["flags"]:
            logger.info("Mass censoring chat")
            if message.chat.id not in censoring["MASS"]:
                censoring["MASS"].append(message.chat.id)
                out += "` → ` Mass censoring\n"
                changed = True
        elif "cmd" in args:
            logger.info("Censoring users")
            users_to_censor = []
            for target in args["cmd"]:
                usr = await client.get_users(target)
                if usr is None:
                    out += f"`[!] → ` {target} not found\n"
                else:
                    users_to_censor.append(usr)
            if "-i" in args["flags"]:
                for u in users_to_censor:
                    if u.id in censoring["FREE"]:
                        censoring["FREE"].remove(u.id)
                        out += f"` → ` {get_username(u)} is no longer immune immune\n"
                        changed = True
            else:
                for u in users_to_censor:
                    if message.chat.id not in censoring["SPEC"]:
                        censoring["SPEC"][message.chat.id] = []
                    censoring["SPEC"][message.chat.id].append(u.id)
                    out += f"` → ` Censoring {get_username(u)}\n"
                    changed = True
        if out != message.text.markdown + "\n":
            await message.edit(out)
        else:
            await message.edit(out + "` → ` Nothing to display")
    except Exception as e:
        traceback.print_exc()
        await message.edit(out + "\n`[!] → ` " + str(e))
    if changed:
        with open("data/censoring.json", "w") as f:
            json.dump(censoring, f)

HELP.add_help(["free", "f"], "stop censoring someone",
            "Stop censoring someone in current chat. Use flag `-mass` to stop mass censorship current chat. " +
            "You can add `-i` to make target immune to mass censoring. More than one target can be specified (separate with spaces). " +
            "Add `-list` flag to list immune users (censor immunity is global but doesn't bypass specific censorship)",
            args="[-mass] [-list] [-i] <targets>")
@alemiBot.on_message(filters.me & newFilterCommand(["free", "f"], list(alemiBot.prefixes), flags=["-list", "-i", "-mass"]))
async def free_cmd(client, message):
    global censoring
    args = message.command
    out = message.text.markdown + "\n"
    changed = False
    try:
        if "-list" in args["flags"]:
            if censoring["FREE"] == []:
                out += "` → ` Nothing to display\n"
            else:
                immune_users = await client.get_users(censoring["FREE"])
                for u in immune_users:
                    out += f"` → ` {get_username(u)}\n"
        elif "-mass" in args["flags"]:
            logger.info("Disabling mass censorship")
            censoring["MASS"].remove(message.chat.id)
            out += "` → ` Restored freedom of speech\n"
            changed = True
        elif "cmd" in args:
            logger.info("Freeing censored users")
            users_to_free = []
            for target in args["cmd"]:
                usr = await client.get_users(target)
                if usr is None:
                    out += f"`[!] → ` {target} not found\n"
                else:
                    users_to_free.append(usr)
            if "-i" in args["flags"]:
                for u in users_to_free:
                    censoring["FREE"].append(u.id)
                    out += f"` → ` {get_username(u)} is now immune\n"
                    changed = True
            else:
                for u in users_to_free:
                    if u.id in censoring["SPEC"][message.chat.id]:
                        censoring["SPEC"][message.chat.id].remove(u.id)
                        out += f"` → ` Freeing {get_username(u)}\n"
                        changed = True
        if out != message.text.markdown + "\n":
            await message.edit(out)
        else:
            await message.edit(out + "` → ` Nothing to display")
    except Exception as e:
        traceback.print_exc()
        await message.edit(out + "\n`[!] → ` " + str(e))
    if changed:
        with open("data/censoring.json", "w") as f:
            json.dump(censoring, f)

@alemiBot.on_message(group=9)
async def bully(client, message):
    if message.edit_date is not None:
        return # pyrogram gets edit events as message events!
    if message.chat is None or is_me(message):
        return # can't censor messages outside of chats or from self
    if message.from_user is None:
        return # Don't censory anonymous msgs
    if message.chat.id in censoring["MASS"] \
    and message.from_user.id not in censoring["FREE"]:
        await message.delete()
        logger.info("Get bullied")
    else:
        if message.chat.id not in censoring["SPEC"] \
        or message.from_user.id not in censoring["SPEC"][message.chat.id]:
            return # Don't censor innocents!
        await message.delete()
        logger.info("Get bullied noob")
    await client.set_offline()

HELP.add_help(["spam", "flood"], "pretty self explainatory",
            "will send many (`-n`) messages in this chat at a specific (`-t`) interval. " +
            "If no number is given, will default to 3. If no interval is specified, " +
            "messages will be sent as soon as possible. You can reply to a message and " +
            "all spammed msgs will reply to that one too. If you add `-delme`, messages will be " +
            "immediately deleted. To stop an ongoing spam, you can do `.spam -cancel`.",
            args="[-cancel] [-n <n>] [-t <t>] <text>")
@alemiBot.on_message(filters.me & newFilterCommand("spam", list(alemiBot.prefixes), options={
    "number" : ["-n"],
    "time" : ["-t"],
}, flags=["-cancel"]))
async def spam(client, message):
    global INTERRUPT
    args = message.command
    if "-cancel" in args["flags"]:
        INTERRUPT = True
        return
    wait = 0
    number = 3
    text = "."
    delme = False
    try:
        if "arg" in args:
            delme = args["arg"].endswith("-delme")
            text = args["arg"].replace("-delme", "") # in case
        if "time" in args:
            wait = float(args["time"])
        if "number" in args:
            number = int(args["number"])
        elif text.split(" ", 1)[0].isnumeric(): # this is to support how it worked originally
            number = int(text.split(" ", 1)[0])
            text = text.split(" ", 1)[1]
        logger.info(f"Spamming \"{text}\" for {number} times")
        extra = {}
        if message.reply_to_message is not None:
            extra["reply_to_message_id"] = message.reply_to_message.message_id
        for i in range(number):
            msg = await client.send_message(message.chat.id, text, **extra)
            if delme:
                await msg.delete()
            await asyncio.sleep(wait)
            if INTERRUPT:
                INTERRUPT = False
                await message.edit(message.text.markdown + f"\n` → ` Canceled after {i} events")
                break
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))

