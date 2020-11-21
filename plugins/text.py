import asyncio
import secrets
import subprocess
import time
import re
import traceback

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
                args="[-t <time>] [-b <batch>] <text>")
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"^[\.\/](?:sl|slow)(?: |)(?P<timer>-t [0-9.]+|)(?: |)(?P<batch>-b [0-9]+|)(?P<text>.*)"
), group=2)
async def slowtype(client, message):
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
            await client.send_chat_action(message.chat.id, "typing")
            await t # does this work? I should read asyncio docs
    except:
        traceback.print_exc()
        pass # msg was deleted probably
    await client.send_chat_action(message.chat.id, "cancel")

HELP.add_help(["rc", "randomcase"], "make text randomly capitalized",
                "will edit message applying random capitalization to every letter, like the spongebob meme.")
@alemiBot.on_message(filters.me & filters.command(["rc", "randomcase"], list(alemiBot.prefixes)), group=2)
async def randomcase(client, message):
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
async def shrug(client, message):
    print(f" [ ¯\_(ツ)_/¯ ]")
    await message.edit(re.sub(r"[\.\/\!]shrug","¯\_(ツ)_/¯", message.text.markdown))

@alemiBot.on_message(filters.me & filters.regex(pattern=r"<-|->|=>|<="), group=3)
async def replace_arrows(client, message):
    print(" [ arrow! ]")
    await message.edit(message.text.markdown.replace("<-", "←")
                                            .replace("->", "→")
                                            .replace("=>", "⇨")
                                            .replace("<=", "⇦"))


HELP.add_help("figlet", "make a figlet art",
                "run figlet and make a text art. You can specify a font (`-f`), or request a random one (`-r`). " +
                "Get list of available fonts with `-list`.", args="[-l] [-r | -f <font>] [-w <n>]", public=True)
@alemiBot.on_message(is_allowed & filters.regex(pattern=
    r"^[\.\/]figlet(?: |)(?:(?P<list>-l)|(?P<font>-f [^ ]+)|(?P<random>-r)|)(?: |)(?P<width>-w [0-9]+|)(?: |)(?P<text>.*)"
))
async def figlettext(client, message):
    args = message.matches[0]
    if args["list"] == "-l":
        msg = f"` → ` **Figlet fonts : ({len(FIGLET_FONTS)})\n```[ "
        msg += " ".join(FIGLET_FONTS)
        msg += " ]```"
        return await edit_or_reply(message, msg)
    width = 30
    if args["width"].startswith("-w "):
        width = int(args["width"].replace("-w ", ""))
    font = "slant"
    if args["random"] == "-r":
        font = secrets.choice(FIGLET_FONTS)
    elif args["font"] is not None and args["font"] != "":
        f = args["font"].replace("-f ", "")
        if f != "" and f in FIGLET_FONTS:
            font = f
    if args["text"] == "":
        return
    print(f" [ figlet-ing {args['text']} ]")
    result = pyfiglet.figlet_format(args["text"], font=font, width=width)
    await edit_or_reply(message, "<code> →\n" + result + "</code>", parse_mode="html")
    await client.set_offline()

HELP.add_help("fortune", "do you feel fortunate!?",
                "run `fortune` to get a random sentence. Like fortune bisquits!", public=True)
@alemiBot.on_message(is_allowed & filters.command(["fortune"], list(alemiBot.prefixes)))
async def fortune(client, message):
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await edit_or_reply(message, "``` → " + output + "```")
    except Exception as e:
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()
