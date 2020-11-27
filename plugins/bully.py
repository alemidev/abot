import asyncio
import subprocess
import traceback
import logging
import re

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from util.parse import CommandParser

from plugins.help import HelpCategory

logger = logging.getLogger(__name__)

HELP = HelpCategory("BULLY")

censoring = {}

HELP.add_help(["censor"], "start censoring a chat",
            "will delete any message sent in this chat from target. If no target " +
            "is specified, all messages will be deleted as soon as they arrive",
            args="[<target>]")
@alemiBot.on_message(filters.me & filters.command(["censor","bully"], list(alemiBot.prefixes)))
async def startcensor(client, message):
    logger.info("Censoring new chat")
    target = None
    if len(message.command) > 1:
        target = message.command[1]
    if target in { None, "@all", "@everyone" }:
        censoring[message.chat.id] = None
    else:
        tgt = await client.get_users(target)
        if target is None:
            return
        if message.chat.id not in censoring \
        or censoring[message.chat.id] is None:
            censoring[message.chat.id] = []
        censoring[message.chat.id].append(tgt.id)
    await message.edit(message.text.markdown + f"\n` → ` Censoring {target if target is not None else 'everyone'}")

HELP.add_help("stop", "stop censoring a chat",
            "typing .stop in a chat that is being censored will stop all censoring")
@alemiBot.on_message(group=9)
async def bully(client, message):
    if message.edit_date is not None:
        return # pyrogram gets edit events as message events!
    if message.chat is None:
        return # can't censor messages outside of chats
    if message.chat.id in censoring:
        if message.from_user is not None and message.from_user.is_self \
        and message.text.startswith(".stop"):
            censoring.pop(message.chat.id, None)
            await message.edit(message.text.markdown + "\n` → ` You can speak again")
            logger.info("No longer censoring a chat")
        else:
            if censoring[message.chat.id] is None:
                await message.delete()
                logger.info("Get bullied")
            else:
                if message.from_user is None:
                    return
                if message.from_user.id in censoring[message.chat.id]:
                    await message.delete()
                    logger.info("Get bullied")
        await client.set_offline()

HELP.add_help(["spam", "flood"], "pretty self explainatory",
            "will send many (`-n`) messages in this chat at a specific (`-t`) interval. " +
            "If no number is given, will default to 3. If no interval is specified, " +
            "messages will be sent as soon as possible. You can reply to a message and " +
            "all spammed msgs will reply to that one too. If you add `-delme`, messages will be " +
            "immediately deleted.", args="[-n <n>] [-t <t>] <text>")
@alemiBot.on_message(filters.me & filters.command("spam", list(alemiBot.prefixes)))
async def spam(client, message):
    args = CommandParser({
        "number" : ["-n"],
        "time" : ["-t"],
    }).parse(message.command)
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
        if message.reply_to_message is not None:
            for i in range(number):
                msg = await message.reply_to_message.reply(text)
                if delme:
                    await msg.delete()
                await asyncio.sleep(wait) 
        else:
            for i in range(number):
                msg = await client.send_message(message.chat.id, text)
                if delme:
                    await msg.delete()
                await asyncio.sleep(wait) 
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))

