import random
import asyncio
import subprocess

from telethon import events

from util import can_react, set_offline
from util.globals import PREFIX

# make character random case (lIkE tHiS)
@events.register(events.NewMessage(
        pattern=r"{p}(?:randomcase|rc) (?P<text>.*)".format(p=PREFIX), outgoing=True))
async def randomcase(event):
    if not can_react(event.chat_id):
        return
    print(f" [ making message randomly capitalized ]")
    text = event.pattern_match.group("text")
    if text == "":
        return 
    msg = "" # omg this part is done so badly
    val = 0  # but I want a kinda imbalanced random
    upper = False
    for c in text:
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
@events.register(events.NewMessage(pattern=r"{p}shrug".format(p=PREFIX)))
async def shrug(event):
    if not can_react(event.chat_id):
        return
    print(f" [ ¯\_(ツ)_/¯ ]")
    if event.out:
        await event.message.edit(r'¯\_(ツ)_/¯')
    else:
        await event.reply(r'¯\_(ツ)_/¯')
    await set_offline(event.client)

# Run fortune
@events.register(events.NewMessage(pattern=r"{p}fortune".format(p=PREFIX)))
async def fortune(event):
    if not can_react(event.chat_id):
        return
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        if event.out:
            await event.message.edit(event.raw_text + "\n``` → " + output + "```")
        else:
            await event.message.reply("``` → " + output + "```")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Roll dice
@events.register(events.NewMessage(pattern=r"{p}roll(?: d| |d)(?P<max>[0-9]+)".format(p=PREFIX)))
async def roll(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = int(event.pattern_match.group("max"))
        print(f" [ rolling d{arg} ]")
        n = random.randint(1, arg)
        if event.out:
            await event.message.edit(event.raw_text + "\n` → ` **{n}**")
        else:
            await event.message.reply(f"` → **{n}**`")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

class TextModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(randomcase)
        self.helptext += "`→ .randomcase <message> ` maKe mEsSAgEs lIkE tHIs *\n"

        client.add_event_handler(shrug)
        self.helptext += "`→ .shrug ` replace or reply with shrug composite emote\n"

        client.add_event_handler(fortune)
        self.helptext += "`→ .fortune ` you feel lucky!?\n"

        client.add_event_handler(roll)
        self.helptext += "`→ .roll d<n> ` get a random number from 1 to n (incl)\n"

        print(" [ Registered Text Modules ]")
