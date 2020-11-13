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
@events.register(events.NewMessage(
    pattern=r"{p}(?:rand|roll)(?: |)(?:(?P<max>d[0-9]+)|(?P<values>.*))".format(p=PREFIX)))
async def rand(event):
    if not can_react(event.chat_id):
        return
    args = event.pattern_match.groupdict()
    try:
        c = "N/A"
        if "max" in args and args["max"] not in [ "", None ]: # this checking is kinda lame
            maxval = int(args["max"].replace("d", ""))
            print(f" [ rolling d{maxval} ]")
            c = random.randint(1, maxval)
        elif "values" in args and args["values"] not in [ "", None ]:
            choices = args["values"].split(" ")
            c = random.choice(choices)[0]
        if event.out:
            await event.message.edit(event.raw_text + f"\n` → ` **{c}**")
        else:
            await event.message.reply(f"` → **{c}**`")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Let me google that for you
@events.register(events.NewMessage(pattern=r"{p}lmgtfy(?: |)(?P<query>.*)".format(p=PREFIX)))
async def lmgtfy(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group("query").replace(" ", "+")
        print(f" [ lmgtfy {arg} ]")
        if event.out:
            await event.message.edit(event.raw_text + f"\n` → ` http://letmegooglethat.com/?q={arg}")
        else:
            await event.message.reply(f"` → ` http://letmegooglethat.com/?q={arg}")
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

        client.add_event_handler(rand)
        self.helptext += "`→ .rand [max] [choices] ` get random number or element\n"

        client.add_event_handler(lmgtfy)
        self.helptext += "`→ .lmgtfy <something> ` make a lmgtfy link\n"

        print(" [ Registered Text Modules ]")
