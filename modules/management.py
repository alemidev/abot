import random
import asyncio
import subprocess

from telethon import events

from util import can_react, set_offline, ignore_chat

# Delete message immediately after it being sent
@events.register(events.NewMessage(pattern=r"\.delme"))
async def deleteme(event):
    if event.out:
        print(" [ deleting sent message ]")
        await event.message.delete()
        await set_offline(event.client)

# Delete last X messages you sent
@events.register(events.NewMessage(pattern=r"\.purge (.*)"))
async def purge(event):
    if event.out:
        number = int(event.pattern_match.group(1))
        me = await event.client.get_me()
        print(f" [ deleting last {number} message ]")
        n = 0
        async for message in event.client.iter_messages(await event.get_chat()):
            if message.sender_id == me.id:
                await message.delete()
                n += 1
            if n >= number:
                break
        await event.message.delete()
        await set_offline(event.client)

# Delete last X messages sent by anyone
@events.register(events.NewMessage(pattern=r"\.censor (.*)"))
async def censor(event):
    if event.out:
        number = int(event.pattern_match.group(1))
        print(f" [ censoring last {number} message ]")
        n = 0
        async for message in event.client.iter_messages(await event.get_chat()):
            try:
                await message.delete()
            except:
                pass # in case you can't delete messages for others
            n += 1
            if n >= number:
                break
        await event.message.delete()
        await set_offline(event.client)

# Set chat as ignored for a while
@events.register(events.NewMessage(pattern=r"\.ignore (.*)"))
async def ignore(event):
    if event.out:
        try:
            number = int(event.pattern_match.group(1))
            print(f" [ muting chat ]")
            ignore_chat(event.chat_id, number)
        except: pass

# Spam message x times
#  this command is not really group-management but seems more
#  appropriate here than in modules/text.py
@events.register(events.NewMessage(pattern=r"\.spam " +
                r"([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]) (.*)"))
async def spam(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        try:
            number = int(event.pattern_match.group(1))
            mess = event.pattern_match.group(2)
            print(f" [ spamming \"{mess}\" for {number} times ]")
            
            if event.is_reply:
                msg = await event.get_reply_message()
                for i in range(number):
                    await msg.reply(mess)
            else:
                for i in range(number):
                    await event.respond(mess)
        except Exception as e:
            await event.reply("`[!] → ` " + str(e))
    else:
        await event.reply("` → ◔_◔ ` u wish")
    await set_offline(event.client)

class ManagementModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(deleteme)
        self.helptext += "`→ .delete ` delete sent message immediately *\n"

        client.add_event_handler(purge)
        self.helptext += "`→ .purge <number> ` delete last <n> sent messages *\n"

        client.add_event_handler(censor)
        self.helptext += "`→ .censor <number> ` delete last <n> from ANYONE *\n"

        client.add_event_handler(ignore)
        self.helptext += "`→ .ignore <seconds> ` ignore commands in this chat *\n"

        client.add_event_handler(spam)
        self.helptext += "`→ .spam <number> <message> ` self explainatory *\n"

        print(" [ Registered Management Modules ]")
