import asyncio
import subprocess
import traceback

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed
from plugins.help import HelpCategory

HELP = HelpCategory("BULLY")

censoring = {}

HELP.add_help("stop", "stop censoring a chat",
            "typing .stop in a chat that is being censored will stop all censoring")
@alemiBot.on_message(group=9)
async def bully(client, message):
    if message.edit_date is not None:
        return # pyrogram gets edit events as message events!
    if message.chat.id in censoring:
        if message.from_user is not None and message.from_user.is_self \
        and message.text.startswith(".stop"):
            censoring.pop(message.chat.id, None)
            await message.edit(message.text + "\n` → ` You can speak again")
            print(" [ No longer censoring a chat ]")
        else:
            if censoring[message.chat.id] is None:
                await message.delete()
            else:
                if message.from_user is None:
                    return
                if message.from_user.id in censoring[message.chat.id]:
                    await message.delete()

HELP.add_help(["censor", "bully"], "start censoring a chat",
            "will delete any message sent in this chat from target. If no target " +
            "is specified, all messages will be deleted as soon as they arrive",
            args="[target]")
@alemiBot.on_message(filters.me & filters.command(["censor","bully"], prefixes=".") &
    filters.regex(pattern=r"^.(?:censor|bully)(?: |)(?P<target>@[^ ]+|)"
))
async def startcensor(client, message):
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
    await message.edit(message.text + f"\n` → ` Censoring {target}")
    print(" [ Censoring new chat ]")

HELP.add_help(["spam", "flood"], "pretty self explainatory",
            "will send many messages in this chat at a specific interval. " +
            "If no number is given, will default to 5. If no interval is specified, " +
            "messages will be sent as soon as possible. You can reply to a message and " +
            "all spammed msgs will reply to that one too",
            args="[-n] [-t]")
@alemiBot.on_message(filters.me & filters.command("spam", prefixes=".") & filters.regex(
        pattern=r"^.spam(?: |)(?P<number>(?:-n |)[0-9]+|)(?: |)(?P<time>-t [0-9.]+|)(?P<text>.*)"
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
        print(f" [ spamming \"{args['text']}\" for {number} times ]")
        if message.reply_to_message is not None:
            for i in range(number):
                await message.reply_to_message.reply(args['text'])
                await asyncio.sleep(wait) 
        else:
            for i in range(number):
                await client.send_message(message.chat.id, args['text'])
                await asyncio.sleep(wait) 
    except Exception as e:
        await message.edit(message.text + "`[!] → ` " + str(e))
