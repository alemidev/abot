import asyncio
import secrets
import subprocess
import time
import re
import traceback

from collections import Counter

from pyrogram import filters

from util import batchify
from util.parse import cleartermcolor
from util.permission import is_allowed
from util.message import edit_or_reply

from bot import alemiBot

import pyfiglet

from plugins.help import HelpCategory

HELP = HelpCategory("TEXT")

FIGLET_FONTS = pyfiglet.FigletFont.getFonts()

HELP.add_help(["slow", "sl"], "make text appear slowly",
                "edit message adding batch of characters every time. If no batch size is " +
                "given, it will default to 1. If no time is given, it will default to 0.5s.",
                args="[-t] [-b] <text>")
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"^[\.\/](?:sl|slow)(?: |)(?P<timer>-t [0-9.]+|)(?: |)(?P<batch>-b [0-9]+|)(?P<text>.*)"
), group=2)
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

HELP.add_help(["cd", "countdown"], "count down",
                "will edit message to show a countdown. If no time is given, it will be 5s.",
                args="[time]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["countdown", "cd"], list(alemiBot.prefixes)), group=2)
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

HELP.add_help(["rc", "randomcase"], "make text randomly capitalized",
                "will edit message applying random capitalization to every letter, like the spongebob meme.")
@alemiBot.on_message(filters.me & filters.command(["rc", "randomcase"], list(alemiBot.prefixes)), group=2)
async def randomcase(_, message):
    print(f" [ making message randomly capitalized ]")
    text = re.sub("[\.\/](?:rc|randomcase)(?: |)", "", message.text.markdown)
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

HELP.add_help("shrug", "¯\_(ツ)_/¯", "will replace `.shrug` or `/shrug` or `!shrug` anywhere "+
                "in yor message with the composite emoji. (this will ignore your custom prefixes)")
@alemiBot.on_message(filters.me & filters.regex(pattern="[" + "\\".join(list(alemiBot.prefixes)) + "]shrug"), group=2)
async def shrug(_, message):
    print(f" [ ¯\_(ツ)_/¯ ]")
    await message.edit(re.sub(r"[\.\/\!]shrug","¯\_(ツ)_/¯", message.text.markdown))

@alemiBot.on_message(filters.me & filters.regex(pattern=r"<-|->|=>|<="), group=3)
async def replace_arrows(_, message):
    await message.edit(message.text.markdown.replace("<-", "←")
                                            .replace("->", "→")
                                            .replace("=>", "⇨")
                                            .replace("<=", "⇦"))


HELP.add_help("figlet", "make a figlet art",
                "run figlet and make a text art. You can specify a font (`-f`), or request a random one (`-r`). " +
                "Get list of available fonts with `-list`.", args="[-l] [-f] [-r]", public=True)
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
        return await edit_or_reply(message, msg)
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
    await edit_or_reply(message, "<code> →\n" + result + "</code>", parse_mode="html")

HELP.add_help("fortune", "do you feel fortunate!?",
                "run `fortune` to get a random sentence. Like fortune bisquits!", public=True)
@alemiBot.on_message(is_allowed & filters.command(["fortune"], list(alemiBot.prefixes)))
async def fortune(_, message):
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await edit_or_reply(message, "``` → " + output + "```")
    except Exception as e:
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help(["rand", "random", "roll"], "get random choices",
                "this can be used as a dice roller (`.roll 3d6`). If a list of choices is given, a random one " +
                "will be chosen from that. If a number is given, it will choose a value from 1 to <n>, both included. " +
                "You can specify how many extractions to make", args="[-n] [choices]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["rand", "random", "roll"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:random|rand|roll)(?: |)(?:(?:(?P<num>[0-9]+|)d(?P<max>[0-9]+))|(?:(?P<batch>-n [0-9]+|)(?: |)(?P<values>.*)))"
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
