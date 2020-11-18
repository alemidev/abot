import asyncio
import secrets
import subprocess
import time
import re
import traceback

from collections import Counter

from pyrogram import filters

from util import set_offline, batchify
from util.parse import cleartermcolor
from util.permission import is_allowed
from util.message import edit_or_reply

from bot import alemiBot

import pyfiglet

FIGLET_FONTS = pyfiglet.FigletFont.getFonts()

# edit message adding characters one at a time
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"^[\.\/](?:sl|slow)(?: |)(?P<timer>-t [0-9.]+|)(?: |)(?P<batch>-b [0-9]+|)(?P<text>.*)"
))
async def slowtype(_, message):
    args = message.matches[0]
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
            if seg.isspace() or seg == "":
                continue # important because sending same message twice causes an exception
            t = asyncio.sleep(interval) # does this "start" the coroutine early?
            await message.edit(msg)
            await t # does this work? I should read asyncio docs
    except:
        traceback.print_exc()
        pass # msg was deleted probably
    # await set_offline(event.client)

def interval(delta):
    if delta > 100:
        return 5
    if delta > 20:
        return 1
    if delta > 10:
        return 0.5
    return 0.25

# Display a countdown
@alemiBot.on_message(is_allowed & filters.command(["countdown", "cd"], prefixes="."))
async def countdown(_, message):
    if message.outgoing:
        tgt_msg = message
    else:
        tgt_msg = await message.reply("` → `")
    end = time.time() + 5
    if len(message.command) > 1:
        try:
            end = time.time() + float(message.command[1])
        except ValueError:
            return await tgt_msg.edit("`[!] → ` argument must be a float")
    msg = tgt_msg.text + "\n` → Countdown ` **{:.1f}**"
    print(f" [ countdown ]")
    while time.time() < end:
        await tgt_msg.edit(msg.format(time.time() - end))
        await asyncio.sleep(interval(end - time.time()))
    await tgt_msg.edit(msg.format(0))

# make character random case (lIkE tHiS)
@alemiBot.on_message(filters.me & filters.command(["rc", "randomcase"], prefixes="."))
async def randomcase(_, message):
    print(f" [ making message randomly capitalized ]")
    text = re.sub("[\.\/](?:rc|randomcase)(?: |)", "", message.text)
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
    await message.edit(msg)

# make character random case (lIkE tHiS)
@alemiBot.on_message(is_allowed & filters.command(["shrug"], prefixes="."))
async def shrug(_, message):
    print(f" [ ¯\_(ツ)_/¯ ]")
    await edit_or_reply(r'¯\_(ツ)_/¯')

# Replace or reply with figlet art
@alemiBot.on_message(is_allowed & filters.regex(pattern=
    r"^[\.\/]figlet(?: |)(?:(?P<list>-l)|(?P<font>-f [^ ]+)|(?P<random>-r)|)(?: |)(?P<text>.*)"
))
async def figlettext(_, message):
    print(f" [ figlet ]")
    args = message.matches[0]
    if args["list"] == "-l":
        msg = f"` → ` **Figlet fonts : ({len(FIGLET_FONTS)})\n```[ "
        msg += " ".join(FIGLET_FONTS)
        msg += " ]```"
        await edit_or_reply(msg)
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
    await edit_or_reply("<code> →\n" + result + "</code>")

# Run fortune
@alemiBot.on_message(is_allowed & filters.command(["fortune"], prefixes="."))
async def fortune(_, message):
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await edit_or_reply("``` → " + output + "```")
    except Exception as e:
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Roll dice
# Replace or reply with figlet art
@alemiBot.on_message(is_allowed & filters.regex(pattern=
    r"^[\.\/](?:random|rand|roll)(?: |)(?:(?:(?P<num>[0-9]+|)d(?P<max>[0-9]+))|(?:(?P<batch>-n [0-9]+|)(?: |)(?P<values>.*)))"
))
async def rand(_, message):
    args = message.matches[0]
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
        elif args["values"] != None and args["values"] != "":
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
                out += "` → Binary " + "".join(str(x) for x in res) + "`\n"
                res = [] # so it won't do the thing below
        for r in res:
            out += f"` → ` **{r}**\n"
        await edit_or_reply(out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# class TextModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ TEXT `\n"
# 
#         client.add_event_handler(slowtype)
#         self.helptext += "`→ .slow [-t n] [-b n] <message> ` type msg slowly\n"
# 
#         client.add_event_handler(countdown)
#         self.helptext += "`→ .cd <time> ` count down time *\n"
# 
#         client.add_event_handler(randomcase)
#         self.helptext += "`→ .rc <message> ` maKe mEsSAgEs lIkE tHIs\n"
# 
#         client.add_event_handler(figlettext)
#         self.helptext += "`→ .figlet [-l]|[-r]|[-f font] <text> ` maKe figlet art *\n"
# 
#         client.add_event_handler(shrug)
#         self.helptext += "`→ .shrug ` replace or reply with shrug composite emote *\n"
# 
#         client.add_event_handler(fortune)
#         self.helptext += "`→ .fortune ` you feel lucky!? *\n"
# 
#         client.add_event_handler(rand)
#         self.helptext += "`→ .rand [n]d[max] | [-n <n>] [vals] ` get random stuff *\n"
# 
#         print(" [ Registered Text Modules ]")
