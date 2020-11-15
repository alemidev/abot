import asyncio
import secrets
import subprocess
import time
import traceback

from collections import Counter

from telethon import events

from util import set_offline, batchify
from util.globals import PREFIX
from util.parse import cleartermcolor
from util.permission import is_allowed

import pyfiglet

FIGLET_FONTS = pyfiglet.FigletFont.getFonts()

# edit message adding characters one at a time
@events.register(events.NewMessage(
        pattern=r"{p}(?:slow|sl)(?: |)(?P<timer>-t [0-9.]+|)(?: |)(?P<batch>-b [0-9]+|)(?P<text>.*)".format(p=PREFIX),
        outgoing=True))
async def slowtype(event):
    args = event.pattern_match.groupdict()
    print(f" [ making text appear slowly ]")
    interval = 0.5
    batchsize = 1
    if args["timer"] != "":
        interval = float(args["timer"].replace("-t ", ""))
    if args["batch"] != "":
        batchsize = int(args["batch"].replace("-b ", ""))
    if args["text"] == "":
        return 
    msg = ""
    try:
        for seg in batchify(args["text"], batchsize):
            msg += seg
            if seg.isspace():
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
    if not event.out and not is_allowed(event.sender_id):
        return
    if event.out:
        tgt_msg = event.message
    else:
        tgt_msg = await event.message.reply("` → `")
    end = time.time() + float(event.pattern_match.group("timer"))
    msg = event.raw_text + "\n` → Countdown ` **{:.1f}**"
    print(f" [ countdown ]")
    while time.time() < end:
        await tgt_msg.edit(msg.format(time.time() - end))
        await asyncio.sleep(interval(end - time.time()))
    await tgt_msg.edit(msg.format(0))
    await set_offline(event.client)

# make character random case (lIkE tHiS)
@events.register(events.NewMessage(
        pattern=r"{p}(?:rc|randomcase)(?: |)(?P<text>.*)".format(p=PREFIX), outgoing=True))
async def randomcase(event):
    print(f" [ making message randomly capitalized ]")
    text = event.pattern_match.group("text")
    if text == "":
        return 
    msg = "" # omg this part is done so badly
    val = 0  # but I want a kinda imbalanced random
    upper = False
    for c in text:
        last = val
        val = secrets.randbelow(4)
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
    if not event.out and not is_allowed(event.sender_id):
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
    if not event.out and not is_allowed(event.sender_id):
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
        font = secrets.choice(FIGLET_FONTS)
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
    if not event.out and not is_allowed(event.sender_id):
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
    pattern=r"{p}(?:rand|roll)(?: |)(?:(?:(?P<num>[0-9]+|)d(?P<max>[0-9]+))|(?:(?P<batch>-n [0-9]+|)(?: |)(?P<values>.*)))".format(p=PREFIX)))
async def rand(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    args = event.pattern_match.groupdict()
    try:
        res = []
        times = 1
        out = ""
        if args["num"] not in [ "", None ]:
            times = int(args["num"])
        elif args["batch"] not in [ "", None ]:
            times = int(args["batch"].replace("-n ", ""))
        if args["max"] not in [ "", None ]: # this checking is kinda lame
            maxval = int(args["max"])
            print(f" [ rolling d{maxval} ]")
            for i in range(times):
                res.append(secrets.randbelow(maxval) + 1)
            if times > 1:
                out += f"`→ Rolled {times}d{maxval}` : **{sum(res)}**\n"
        elif "values" in args and args["values"] not in [ "", None ]:
            choices = args["values"].split(" ")
            print(f" [ rolling {choices} ]")
            for i in range(times):
                res.append(secrets.choice(choices))
            res_count = Counter(res)
            if times > 1:
                out += "`→ Random choice ` **" + res_count.most_common(1)[0][0] + "**\n"
        else:
            choices = [ 1, 0 ]
            print(f" [ rolling {choices} ]")
            for i in range(times):
                res.append(secrets.choice(choices))
            if times > 1:
                out += "`→ Binary " + "".join(str(x) for x in res) + "`\n"
        for r in res:
            out += f"` → ` **{r}**\n"
        if event.out:
            await event.message.edit(event.raw_text + "\n" + out)
        else:
            await event.message.reply(out)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

class TextModules:
    def __init__(self, client):
        self.helptext = "`━━┫ TEXT `\n"

        client.add_event_handler(slowtype)
        self.helptext += "`→ .slow [-t n] [-b n] <message> ` type msg slowly\n"

        client.add_event_handler(countdown)
        self.helptext += "`→ .cd <time> ` count down time *\n"

        client.add_event_handler(randomcase)
        self.helptext += "`→ .rc <message> ` maKe mEsSAgEs lIkE tHIs\n"

        client.add_event_handler(figlettext)
        self.helptext += "`→ .figlet [-l]|[-r]|[-f font] <text> ` maKe figlet art *\n"

        client.add_event_handler(shrug)
        self.helptext += "`→ .shrug ` replace or reply with shrug composite emote *\n"

        client.add_event_handler(fortune)
        self.helptext += "`→ .fortune ` you feel lucky!? *\n"

        client.add_event_handler(rand)
        self.helptext += "`→ .rand [n]d[max] | [-n <n>] [vals] ` get random stuff *\n"

        print(" [ Registered Text Modules ]")
