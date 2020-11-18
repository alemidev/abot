import asyncio
import subprocess
import traceback

from pyrogram import filters

from bot import alemiBot

from util.permission import is_allowed

censoring = {}

# Delete all messages as soon as they arrive
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

# Start bullying a chat
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

# Spam message x times
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

# class BullyModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ BULLY`\n"
# 
#         client.add_event_handler(spam)
#         self.helptext += "`→ .spam [-n] [-t] <message> ` self explainatory\n"
# 
#         client.add_event_handler(bully)
#         client.add_event_handler(startcensor)
#         self.helptext += "`→ .censor [target] ` delete msgs sent by target\n"
#         self.helptext += "`→ .stop ` stop censoring this chat\n"
# 
#         print(" [ Registered Bully Modules ]")
