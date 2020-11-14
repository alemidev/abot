import random
import asyncio
import subprocess
import traceback

from telethon import events

from util import can_react, set_offline
from util.globals import PREFIX

censoring = {}

# Delete all messages as soon as they arrive
@events.register(events.NewMessage)
async def bully(event):
    if event.chat_id in censoring:
        if event.out and event.raw_text.startswith(".stop"):
            censoring.pop(event.chat_id)
            await event.message.edit(event.message.message + "\n` → ` You can speak again")
            print(" [ No longer censoring a chat ]")
        else:
            if censoring[event.chat_id] is None:
                await event.message.delete()
            else:
                sender = await event.client.get_entity(await event.get_input_sender())
                if sender.id in censoring[event.chat_id]:
                    await event.message.delete()

# Start bullying a chat
@events.register(events.NewMessage(
    pattern=r"{p}(?:censor|bully)(?: |)(?P<target>@[^ ]+|)".format(p=PREFIX), outgoing=True))
async def startcensor(event):
    target = event.pattern_match.group("target")
    if target in { "", "@all", "@everyone" }:
        censoring[event.chat_id] = None
    else:
        tgt = await event.client.get_entity(target)
        if target is None:
            return
        if event.chat_id not in censoring:
            censoring[event.chat_id] = []
        elif censoring[event.chat_id] is None:
            censoring[event.chat_id] = []
        censoring[event.chat_id].append(tgt.id)
    await event.message.edit(event.message.message + f"\n` → ` Censoring {target}")
    print(" [ Censoring new chat ]")

# Spam message x times
@events.register(events.NewMessage(
        pattern=r"{p}spam(?: |)(?P<number>(?:-n |)[0-9]+|)(?: |)(?P<time>-t [0-9.]+|)(?P<text>.*)".format(p=PREFIX)))
async def spam(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        args = event.pattern_match.groupdict()
        try:
            if "text" not in args or args["text"] == "":
                return
            wait = 0
            if args["time"] not in [ None, "" ]:
                wait = float(args["time"].replace("-t ", ""))
            number = 5
            if args["number"] not in [ None, "" ]:
                number = int(args["number"].replace("-n ", "")) 
            print(f" [ spamming \"{args['text']}\" for {number} times ]")
            if event.is_reply:
                msg = await event.get_reply_message()
                for i in range(number):
                    await msg.reply(args['text'])
                    await asyncio.sleep(wait) 
            else:
                for i in range(number):
                    await event.respond(args['text'])
                    await asyncio.sleep(wait) 
        except Exception as e:
            await event.reply("`[!] → ` " + str(e))
    else:
        await event.reply("` → ◔_◔ ` u wish")
    await set_offline(event.client)

class BullyModules:
    def __init__(self, client):
        self.helptext = "`━━┫ BULLY`\n"

        client.add_event_handler(spam)
        self.helptext += "`→ .spam [-n] [-t] <message> ` self explainatory *\n"

        client.add_event_handler(bully)
        client.add_event_handler(startcensor)
        self.helptext += "`→ .censor [target]` delete messages from target *\n"
        self.helptext += "`→ .stop ` stop censoring this chat *\n"

        print(" [ Registered Bully Modules ]")
