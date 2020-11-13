import random
import asyncio
import subprocess

from telethon import events

from util import can_react, set_offline

bullied_chats = []
last_msg = None

# Delete all messages as soon as they arrive
@events.register(events.NewMessage)
async def bully(event):
    # chat = await event.get_chat()   # checking the title is a shit way to
    # if hasattr(chat, 'title'):      # check if this is a group but I found
    #     return                      # no better way (for now)
    if event.chat_id in bullied_chats:
        if event.raw_text.startswith(".stop"):
            bullied_chats.remove(event.chat_id)
            await event.message.edit(event.message.message + "\n` → ` You can speak again")
            print(" [ No longer censoring a chat ]")
        else:
            await event.message.delete()


# Start bullying a chat
@events.register(events.NewMessage(pattern=r"\.censor"))
async def startcensor(event):
    if event.out and event.chat_id not in bullied_chats:
        bullied_chats.append(event.chat_id)
        await event.message.edit(event.message.message + "\n` → ` Censoring")
        print(" [ Censoring new chat ]")

# Spam message x times
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

class BullyModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(spam)
        self.helptext += "`→ .spam <number> <message> ` self explainatory *\n"

        client.add_event_handler(bully)
        client.add_event_handler(startcensor)
        self.helptext += "`→ .censor ` delete all further messages *\n"
        self.helptext += "`→ .stop ` stop censoring this chat *\n"

        print(" [ Registered Bully Modules ]")
