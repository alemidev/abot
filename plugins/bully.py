import asyncio
import subprocess
import traceback
import logging
import re

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from plugins.help import HelpCategory

logger = logging.getLogger(__name__)

HELP = HelpCategory("BULLY")

censoring = {}

HELP.add_help(["censor"], "start censoring a chat",
            "will delete any message sent in this chat from target. If no target " +
            "is specified, all messages will be deleted as soon as they arrive",
            args="[<target>]")
@alemiBot.on_message(filters.me & filters.command(["censor","bully"], list(alemiBot.prefixes)) &
    filters.regex(pattern=r"^.(?:censor|bully)(?: |)(?P<target>@[^ ]+|)"
))
async def startcensor(client, message):
    logger.info("Censoring new chat")
    target = message.matches[0]["target"]
    if target in { "", "@all", "@everyone" }:
        censoring[message.chat.id] = None
    else:
        tgt = await client.get_users(target)
        if target is None:
            return
        if message.chat.id not in censoring \
        or censoring[message.chat.id] is None:
            censoring[message.chat.id] = []
        censoring[message.chat.id].append(tgt.id)
    await message.edit(message.text.markdown + f"\n` → ` Censoring {target}")

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
            "will send many messages in this chat at a specific interval. " +
            "If no number is given, will default to 5. If no interval is specified, " +
            "messages will be sent as soon as possible. You can reply to a message and " +
            "all spammed msgs will reply to that one too",
            args="[-n <n>] [-t <t>] <text>")
@alemiBot.on_message(filters.me & filters.command("spam", list(alemiBot.prefixes)) & filters.regex(
        pattern=r"^.spam(?: |)(?P<number>(?:-n |)[0-9]+|)(?: |)(?P<time>-t [0-9.]+|)(?P<text>.*)", flags=re.DOTALL
))
async def spam(client, message):
    args = message.matches[0]
    try:
        if args["text"] == "":
            return
        wait = 0
        if args["time"] is not None and args["time"] != "":
            wait = float(args["time"].replace("-t ", ""))
        number = 5
        if args["number"] is not None and args["number"] != "":
            number = int(args["number"].replace("-n ", "")) 
        logger.info(f"Spamming \"{args['text']}\" for {number} times")
        if message.reply_to_message is not None:
            for i in range(number):
                await message.reply_to_message.reply(args['text'])
                await asyncio.sleep(wait) 
        else:
            for i in range(number):
                await client.send_message(message.chat.id, args['text'])
                await asyncio.sleep(wait) 
    except Exception as e:
        await message.edit(message.text.markdown + "`[!] → ` " + str(e))
