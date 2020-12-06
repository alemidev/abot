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
from util.message import edit_or_reply, is_me, get_text
from util.command import filterCommand

from bot import alemiBot

import pyfiglet

from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

HELP = HelpCategory("TEXT")

FIGLET_FONTS = pyfiglet.FigletFont.getFonts()
FIGLET_FONTS.sort()


HELP.add_help(["slow", "sl"], "make text appear slowly",
                "edit message adding batch of characters every time. If no batch size is " +
                "given, it will default to 1. If no time is given, it will default to 0.5s.",
                args="[-t <time>] [-b <batch>] <text>")
@alemiBot.on_message(filters.me & filterCommand(["slow", "sl"], list(alemiBot.prefixes), options={
        "time" : ["-t"],
        "batch" : ["-b"]
}), group=2)
async def slowtype(client, message):
    args = message.command
    if "arg" not in args:
        return
    logger.info(f"Making text appear slowly")
    interval = 0.5
    batchsize = 1
    if "time" in args:
        interval = float(args["time"])
    if "batch" in args:
        batchsize = int(args["batch"])
    msg = ""
    try:
        for seg in batchify(args["arg"], batchsize):
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
                "will edit message applying random capitalization to every letter, like the spongebob meme.",
                args="<text>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["rc", "randomcase"], list(alemiBot.prefixes)), group=2)
async def randomcase(client, message):
    logger.info(f"Making message randomly capitalized")
    text = message.command["arg"]
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
    if is_me(message):
        await message.edit(msg)
    else:
        await message.reply(msg)
    await client.set_offline()

HELP.add_help("shrug", "¯\_(ツ)_/¯", "will replace `.shrug` anywhere "+
                "in yor message with the composite emoji. (this will ignore your custom prefixes)")
@alemiBot.on_message(filters.me & filters.regex(pattern="[\\" + "\\".join(list(alemiBot.prefixes)) + "]shrug"), group=2)
async def shrug(client, message):
    logger.info(f" ¯\_(ツ)_/¯ ")
    await message.edit(re.sub(r"[\.\/\!]shrug","¯\_(ツ)_/¯", message.text.markdown))

@alemiBot.on_message(filters.me & filters.regex(pattern=r"<-|->|=>|<="), group=3)
async def replace_arrows(client, message):
    logger.info("arrow!")
    await message.edit(message.text.markdown.replace("<-", "←")
                                            .replace("->", "→")
                                            .replace("=>", "⇨")
                                            .replace("<=", "⇦"))


HELP.add_help("figlet", "make a figlet art",
                "run figlet and make a text art. You can specify a font (`-f`), or request a random one (`-r`). " +
                "Get list of available fonts with `-list`. You can specify max figlet width (`-w`), default is 30.",
                args="[-list] [-r | -f <font>] [-w <n>] <text>", public=True)
@alemiBot.on_message(is_allowed & filterCommand("figlet", list(alemiBot.prefixes), options={
    "font" : ["-f", "-font"],
    "width" : ["-w", "-width"]
}, flags=["-list", "-r"]))
async def figlettext(client, message):
    args = message.command
    try:
        if "-list" in args["flags"]:
            msg = f"<code> → </code> <u>Figlet fonts</u> : <b>{len(FIGLET_FONTS)}</b>\n[ "
            msg += " ".join(FIGLET_FONTS)
            msg += " ]"
            return await edit_or_reply(message, msg, parse_mode='html')

        if "arg" not in args:
            return # no text to figlet!

        width = 30
        if "width" in args:
            width = int(args["width"])
        font = "slant"
        if "-r" in args["flags"]:
            font = secrets.choice(FIGLET_FONTS)
        elif "font" in args:
            f = args["font"]
            if f != "" and f in FIGLET_FONTS:
                font = f

        logger.info(f"figlet-ing {args['arg']}")
        result = pyfiglet.figlet_format(args["arg"], font=font, width=width)
        await edit_or_reply(message, "<code> →\n" + result + "</code>", parse_mode="html")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help("fortune", "do you feel fortunate!?",
                "run `fortune` to get a random sentence. Like fortune bisquits!", args="[-cow]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["fortune"], list(alemiBot.prefixes), flags=["-cow"]))
async def fortune(client, message):
    try:
        logger.info(f"Running command \"fortune\"")
        result = b""
        if "-cow" in message.command["flags"]:
            result = subprocess.run(["fortune", "|", "cowsay", "-W", "30"], capture_output=True)
        else:
            result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await edit_or_reply(message, "``` → " + output + "```")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["freq", "frequent"], "find frequent words in messages",
                "find most used words in last messages. If no number is given, will search only " +
                "last 20 messages. By default, 5 most frequent words are shown, but number of results " +
                "can be changed with `-r`.", args="[-r <n>] [n]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["freq", "frequent"], list(alemiBot.prefixes), options={
    "results" : ["-r", "-res"]
}))
async def cmd_frequency(client, message):
    results = int(message.command["results"]) if "results" in message.command else 5
    number = int(message.command["cmd"][0]) if "cmd" in message.command else 20
    try:
        logger.info(f"Counting {results} most frequent words in last {number} messages")
        response = await edit_or_reply(message, f"` → ` Counting words in messages")
        await client.send_chat_action(message.chat.id, "playing")
        buf = ""
        count = 0
        async for msg in client.iter_history(message.chat.id, limit=number):
            buf += get_text(msg)
            count += 1
            if count % 20 == 0:
                await response.edit(response.text + f" [{count}/{number}]")
        count = Counter(buf.replace("\n", "").split()).most_common()
        output = f"`→ ` **{results}** most frequent words in last **{number}** messages:\n"
        for i in range(results):
            output += f"`{i+1:02d}]{'-'*(results-i-1)}>` `{count[i][0]}` `({count[i][1]})`\n"
        await response.edit(output)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()
