import asyncio
import secrets
import re
import time
import traceback

from collections import Counter

from pyrogram import filters

from util.permission import is_allowed
from util.message import edit_or_reply, is_me

from googletrans import Translator

from bot import alemiBot

from plugins.help import HelpCategory

translator = Translator()

HELP = HelpCategory("UTIL")

def interval(delta):
    if delta > 100:
        return 10
    if delta > 50:
        return 5
    if delta > 20:
        return 3
    if delta > 10:
        return 1
    if delta > 5:
        return 0.5
    if delta > 2:
        return 0.25
    return 0

HELP.add_help(["cd", "countdown"], "count down",
                "will edit message to show a countdown. If no time is given, it will be 5s.",
                args="[time]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["countdown", "cd"], list(alemiBot.prefixes)), group=2)
async def countdown(_, message):
    if is_me(message):
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
    last = ""
    print(f" [ countdown ]")
    while time.time() < end:
        curr = msg.format(time.time() - end)
        if curr != last: # with fast counting down at the end it may try to edit with same value
            await tgt_msg.edit(msg.format(time.time() - end))
            last = curr
        await asyncio.sleep(interval(end - time.time()))
    await tgt_msg.edit(msg.format(0))

HELP.add_help(["rand", "random", "roll"], "get random choices",
                "this can be used as a dice roller (`.roll 3d6`). If a list of choices is given, a random one " +
                "will be chosen from that. If a number is given, it will choose a value from 1 to <n>, both included. " +
                "You can specify how many extractions to make", args="[-n] [choices]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["rand", "random", "roll"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:random|rand|roll)(?: |)(?:(?:(?P<num>[0-9]+|)d(?P<max>[0-9]+))|(?:(?P<batch>-n [0-9]+|)(?: |)(?P<values>.*)))"
))
async def rand_cmd(_, message):
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
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help(["translate", "tran", "tr"], "translate to/from",
                "translate text from a language (autodetected if not specified, `-s`) to another " +
                "specified lang (defaults to eng, `-d`). It will show the confidence for detected lang. This " +
                "uses google translate. The lang codes must be 2 letter long (en, ja...)", args="[-s] [-d]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["translate", "tran", "tr"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:translate|tran|tr)(?: |)(?P<src>-s [^ ]+|)(?: |)(?P<dest>-d [^ ]+|)(?: |)(?P<text>.*)"
))
async def translate_cmd(_, message):
    args = message.matches[0]
    if args["text"] is None or args["text"] == "":
        return await edit_or_reply(message, "`[!] → ` Nothing to translate")
    tr_options = {}
    if args["src"].startswith("-s "):
        tr_options["src"] = args["src"].replace("-s ", "")
    if args["dest"].startswith("-d "):
        tr_options["dest"] = args["dest"].replace("-d ", "")
    try:
        q = args["text"]
        res = translator.translate(q, **tr_options)
        out = f"`[{res.extra_data['confidence']:.2f}] → ` {res.text}"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
