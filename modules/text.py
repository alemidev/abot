import random
import asyncio
import subprocess

from telethon import events

from util import can_react, set_offline

# Replace spaces with clap emoji
@events.register(events.NewMessage(pattern=r"\.clap "))
async def claps(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        print(f" [ replacing spaces with claps ]")
        await event.message.edit(event.raw_text.replace(".clap ","").replace(" ", "👏"))
    await set_offline(event.client)

# make character random case (lIkE tHiS)
@events.register(events.NewMessage(pattern=r"\.randomcase "))
async def randomcase(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        print(f" [ making message randomly capitalized ]")
        msg = "" # omg this part is done so badly
        val = 0  # but I want a kinda imbalanced random
        upper = False
        for c in event.raw_text.lower().replace(".randomcase ", ""):
            last = val
            val = random.randint(0, 3)
            if val > 2:
                msg += c.upper()
                upper = True
            elif val < 1:
                msg += c
                upper = False
            else:
                if upper:
                    msg += c
                    upper = False
                else:
                    msg += c.upper()
                    upper = True
        await event.message.edit(msg)
    await set_offline(event.client)

# Replace .shrug with shrug emoji (or reply with one)
@events.register(events.NewMessage(pattern=r"\.shrug"))
async def shrug(event):
    if not can_react(event.chat_id):
        return
    print(f" [ ¯\_(ツ)_/¯ ]")
    if event.out:
        await event.message.edit(r'¯\_(ツ)_/¯')
    else:
        await event.reply(r'¯\_(ツ)_/¯')
    await set_offline(event.client)

# Delete message immediately after it being sent
@events.register(events.NewMessage(pattern=r"\.delete"))
async def deleteme(event):
    if event.out:
        print(f" [ deleting last message ]")
        await event.message.delete()
        await set_offline(event.client)

# Run fortune
@events.register(events.NewMessage(pattern=r"\.fortune"))
async def fortune(event):
    if not can_react(event.chat_id):
        return
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await event.message.reply("```" + output + "```")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Roll dice
@events.register(events.NewMessage(pattern=r"\.roll (.*)"))
async def roll(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = int(event.pattern_match.group(1).replace("d",""))
        print(f" [ rolling d{arg} ]")
        await event.message.reply(f"` → {random.randint(1, arg)}`")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

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

class TextModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(randomcase)
        self.helptext += "`→ .randomcase <message> ` maKe mEsSAgE cASe RaNdOMizEd *\n"

        client.add_event_handler(claps)
        self.helptext += "`→ .clap <message> ` replace spaces with 👏 in message *\n"

        client.add_event_handler(shrug)
        self.helptext += "`→ .shrug ` replace or reply with shrug composite emote\n"

        client.add_event_handler(deleteme)
        self.helptext += "`→ .delete ` delete sent message immediately *\n"

        client.add_event_handler(fortune)
        self.helptext += "`→ .fortune ` you feel lucky!?\n"

        client.add_event_handler(roll)
        self.helptext += "`→ .roll d<n> ` roll a virtual dice with n faces\n"

        client.add_event_handler(spam)
        self.helptext += "`→ .spam <number> <message> ` self explainatory *\n"

        print(" [ Registered Text Modules ]")
