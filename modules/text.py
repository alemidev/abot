import random
import asyncio
import random
import subprocess
import time
import traceback

from telethon import events

from util import can_react, set_offline, batchify
from util.globals import PREFIX
from util.parse import cleartermcolor

import pyfiglet

FIGLET_FONTS = pyfiglet.FigletFont.getFonts()

# edit message adding characters one at a time
@events.register(events.NewMessage(
        pattern=r"{p}(?:slow|sl)(?: |)(?P<timer>-t [0-9.]+|)(?: |)(?P<text>.*)".format(p=PREFIX), outgoing=True))
async def slowtype(event):
    if not can_react(event.chat_id):
        return
    args = event.pattern_match.groupdict()
    print(f" [ making text appear slowly ]")
    interval = 0.5
    if args["timer"] != "":
        interval = float(args["timer"].replace("-t ", ""))
    if args["text"] == "":
        return 
    msg = ""
    try:
        for c in args["text"]:
            msg += c
            if c.isspace():
                continue # important because sending same message twice causes an exception
            t = asyncio.sleep(interval) # does this "start" the coroutine early?
            await event.message.edit(msg)
            await t # does this work? I should read asyncio docs
    except:
        traceback.print_exc()
        pass # msg was deleted probably
    await set_offline(event.client)

def interval(delta):
    if delta > 100:
        return 5
    if delta > 20:
        return 1
    if delta > 10:
        return 0.5
    return 0.25

# edit message adding characters one at a time
@events.register(events.NewMessage(
        pattern=r"{p}(?:countdown|cd)(?: |)(?P<timer>[0-9.]+)".format(p=PREFIX)))
async def countdown(event):
    if not can_react(event.chat_id):
        return
    end = time.time() + float(event.pattern_match.group("timer"))
    msg = event.raw_text + "\n` → Countdown ` **{:.1f}**"
    print(f" [ countdown ]")
    while time.time() < end:
        await event.message.edit(msg.format(time.time() - end))
        await asyncio.sleep(interval(end - time.time()))
    await event.message.edit(msg.format(0))
    await set_offline(event.client)

# make character random case (lIkE tHiS)
@events.register(events.NewMessage(
        pattern=r"{p}(?:rc|randomcase)(?: |)(?P<text>.*)".format(p=PREFIX), outgoing=True))
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

# Replace or reply with figlet art
@events.register(events.NewMessage(
    pattern=r"{p}figlet(?: |)(?:(?P<list>-l)|(?P<font>-f [^ ]+)|(?P<random>-r)|)(?: |)(?P<text>.*)".format(p=PREFIX)))
async def figlettext(event):
    if not can_react(event.chat_id):
        return
    print(f" [ figlet ]")
    args = event.pattern_match.groupdict()
    if args["list"] == "-l":
        msg = f"` → ` **Figlet fonts : ({len(FIGLET_FONTS)})\n```[ "
        msg += " ".join(FIGLET_FONTS)
        msg += " ]```"
        for m in batchify(msg, 4090):
            await event.message.reply(m)
        return
    font = "slant"
    if args["random"] == "-r":
        font = random.choice(FIGLET_FONTS)
    elif args["font"] is not None and args["font"] != "":
        f = args["font"].replace("-f ", "")
        if f != "" and f in FIGLET_FONTS:
            font = f
    if args["text"] == "":
        return
    result = pyfiglet.figlet_format(args["text"], font=font)
    if event.out:
        await event.message.edit("``` →\n" + result + "```")
    else:
        await event.reply("```→\n" + result + "```")
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
    pattern=r"{p}(?:rand|roll) (?:(?P<max>d[0-9]+)|(?P<values>.*))".format(p=PREFIX)))
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
            print(f" [ rolling {choices} ]")
            c = random.choice(choices)
        else:
            choices = [ "Yes", "No" ]
            print(f" [ rolling {choices} ]")
            c = random.choice(choices)
        if event.out:
            await event.message.edit(event.raw_text + f"\n` → ` **{c}**")
        else:
            await event.message.reply(f"` → ` **{c}**")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

class TextModules:
    def __init__(self, client):
        self.helptext = "`━━┫ TEXT `\n"

        client.add_event_handler(slowtype)
        self.helptext += "`→ .slow [-t n] <message> ` type msg char by char *\n"

        client.add_event_handler(countdown)
        self.helptext += "`→ .cd <time> ` count down time\n"

        client.add_event_handler(randomcase)
        self.helptext += "`→ .rc <message> ` maKe mEsSAgEs lIkE tHIs *\n"

        client.add_event_handler(figlettext)
        self.helptext += "`→ .figlet [-l]|[-r]|[-f font] <text> ` maKe figlet art\n"

        client.add_event_handler(shrug)
        self.helptext += "`→ .shrug ` replace or reply with shrug composite emote\n"

        client.add_event_handler(fortune)
        self.helptext += "`→ .fortune ` you feel lucky!?\n"

        client.add_event_handler(rand)
        self.helptext += "`→ .rand d[max]|[choices] ` get random number or element\n"

        print(" [ Registered Text Modules ]")
