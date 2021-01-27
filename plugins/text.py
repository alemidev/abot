import asyncio
import secrets
import re
from collections import Counter

from pyrogram import filters

from util import batchify
from util.parse import cleartermcolor
from util.permission import is_allowed, is_superuser
from util.message import edit_or_reply, is_me, get_text
from util.chat import get_channel
from util.user import get_username
from util.command import filterCommand

from bot import alemiBot

import pyfiglet
from zalgo_text import zalgo

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
@alemiBot.on_message(is_superuser & filterCommand(["slow", "sl"], list(alemiBot.prefixes), options={
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
    out = ""
    msg = message if is_me(message) else await message.reply("` → ` Ok, starting")
    try:
        for seg in batchify(args["arg"], batchsize):
            out += seg
            if seg.isspace() or seg == "":
                continue # important because sending same message twice causes an exception
            await client.send_chat_action(message.chat.id, "typing")
            await msg.edit(out, parse_mode=None)
            await asyncio.sleep(interval) # does this "start" the coroutine early?
    except:
        logger.exception("Error in .slow command")
        pass # msg was deleted probably
    await client.send_chat_action(message.chat.id, "cancel")

HELP.add_help(["zalgo"], "h̴͔̣̰̲̣̫̲͉̞͍͖̩͖̭͓̬̼ͫ̈͒̊͟͟͠e̵̙͓̼̻̳̝͍̯͇͕̳̝͂̌͐ͫ̍ͬͨ͑̕ ̷̴̢̛̝̙̼̣̔̎̃ͨ͆̾ͣͦ̑c̵̥̼͖̲͓̖͕̭ͦ̽ͮͮ̇ͭͥ͠o̷̷͔̝̮̩͍͉͚͌̿ͥ̔ͧ̉͛ͭ͊̀͜ͅm̵̸̡̰̭͓̩̥͚͍͎̹͖̠̩͙̯̱͙͈͍͉͂ͩ̄̅͗͞e̢̛͖̪̞̐̒̈̓̒́͒̈́̀ͅṡ̡̢̟͖̩̝̣͙̣͔̑́̓̿̊̑̍̉̓͘͢",
                "Will completely fuck up the text with 'zalgo' patterns. You can increase noise " +
                "with the `-n` flag, otherwise will default to 1. You can increase overrall damage with `-d` " +
                "(should be a float from 0 to 1, default to 0). The max number of extra characters per " +
                "letter can be specified with `-max`, with default 10.", args="[-n <n>] [-d <n>] [-max <n>] <text>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["zalgo"], list(alemiBot.prefixes), options={
    "noise" : ["-n", "-noise"],
    "damage" : ["-d", "-damage"],
    "max" : ["-max"]
}), group=2)
async def zalgo_cmd(client, message):
    logger.info(f"Making message zalgoed")
    text = re.sub(r"-delme(?: |)(?:[0-9]+|)", "", message.command["raw"])
    if text == "":
        return 
    try:
        noise = int(message.command["noise"]) if "noise" in message.command else 1
        damage = max(min(float(message.command["damage"]), 1.0), 0.0) if "damage" in message.command else 0
        max_accents = int(message.command["max"]) if "max" in message.command else 10
        z = zalgo.zalgo()
        z.maxAccentsPerLetter = max_accents
        z.numAccentsUp = ( 1+ (damage*noise), 3 * noise )
        z.numAccentsDown = ( 1+ (damage*noise), 3 * noise )
        z.numAccentsMiddle = ( 1+ (damage*noise), 2 * noise )
        out = z.zalgofy(text)

        first = True # kinda ugly but this is kinda different from edit_or_reply
        for batch in batchify(out, 4090):
            if first and is_me(message):
                await message.edit(batch)
            else:
                await client.send_message(message.chat.id, batch)
            first = False
    except Exception as e:
        logger.exception("Error in .zalgo command")
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

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
    await edit_or_reply(message, msg)
    await client.set_offline()

HELP.add_help("shrug", "¯\_(ツ)_/¯", "will replace `.shrug` anywhere "+
                "in yor message with the composite emoji. (this will ignore your custom prefixes)")
@alemiBot.on_message(filters.me & filters.regex(pattern="[\\" + "\\".join(list(alemiBot.prefixes)) + "]shrug"), group=2)
async def shrug(client, message):
    logger.info(f" ¯\_(ツ)_/¯ ")
    await message.edit(re.sub(r"[\.\/\!]shrug","¯\_(ツ)_/¯", message.text.markdown))

HELP.add_help("eyy", "( ͡° ͜ʖ ͡°)", "will replace `.eyy` anywhere "+
                "in yor message with the composite emoji. (this will ignore your custom prefixes)")
@alemiBot.on_message(filters.me & filters.regex(pattern="[\\" + "\\".join(list(alemiBot.prefixes)) + "]eyy"), group=2)
async def eyy_replace(client, message):
    logger.info(f" ( ͡° ͜ʖ ͡°) ")
    await message.edit(re.sub(r"[\.\/\!]eyy","( ͡° ͜ʖ ͡°)", message.text.markdown))

HELP.add_help("holup", "(▀̿Ĺ̯▀̿ ̿)", "will replace `.holup` anywhere "+
                "in yor message with the composite emoji. (this will ignore your custom prefixes)")
@alemiBot.on_message(filters.me & filters.regex(pattern="[\\" + "\\".join(list(alemiBot.prefixes)) + "]holup"), group=2)
async def holup_replace(client, message):
    logger.info(f" (▀̿Ĺ̯▀̿ ̿) ")
    await message.edit(re.sub(r"[\.\/\!]holup","(▀̿Ĺ̯▀̿ ̿)", message.text.markdown))

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
        logger.exception("Error in .figlet command")
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help("fortune", "do you feel fortunate!?",
                "run `fortune` to get a random sentence. Like fortune bisquits!", args="[-cow]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["fortune"], list(alemiBot.prefixes), flags=["-cow"]))
async def fortune(client, message):
    try:
        logger.info(f"Running command \"fortune\"")
        stdout = b""
        if "-cow" in message.command["flags"]:
            proc = await asyncio.create_subprocess_shell(
                    "fortune | cowsay -W 30",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT)
            stdout, stderr = await proc.communicate()
            stdout = b"\n" + stdout
        else:
            proc = await asyncio.create_subprocess_exec(
                    "fortune",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT)
            stdout, stderr = await proc.communicate()
        output = cleartermcolor(stdout.decode())
        await edit_or_reply(message, "``` → " + output + "```")
    except Exception as e:
        logger.exception("Error in .fortune command")
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["freq", "frequent"], "find frequent words in messages",
                "find most used words in last messages. If no number is given, will search only " +
                "last 100 messages. By default, 10 most frequent words are shown, but number of results " +
                "can be changed with `-r`. By default, only words of `len > 3` will be considered. " +
                "A minimum word len can be specified with `-min`. Will search in current group or any specified with `-g`. " +
                "A single user can be specified with `-u` : only messages from that user will count if provided.",
                args="[-r <n>] [-min <n>] [-g <group>] [-u <user>] [n]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["freq", "frequent"], list(alemiBot.prefixes), options={
    "results" : ["-r", "-res"],
    "minlen" : ["-min"],
    "group" : ["-g", "-group"],
    "user" : ["-u", "-user"]
}))
async def cmd_frequency(client, message):
    results = int(message.command["results"]) if "results" in message.command else 10
    number = int(message.command["cmd"][0]) if "cmd" in message.command else 100
    min_len = int(message.command["minlen"]) if "minlen" in message.command else 3
    group = None
    if "group" in message.command:
        val = message.command["group"]
        group = await client.get_chat(int(val) if val.isnumeric() else val)
    else:
        group = message.chat
    user = None
    if "user" in message.command:
        val = message.command["user"]
        user = await client.get_users(int(val) if val.isnumeric() else val)
    try:
        logger.info(f"Counting {results} most frequent words in last {number} messages")
        response = await edit_or_reply(message, f"` → ` Counting word occurrences...")
        words = []
        count = 0
        async for msg in client.iter_history(group.id, limit=number):
            if not user or user.id == msg.from_user.id:
                words += [ w for w in re.sub(r"[^0-9a-zA-Z\s\n]+", "", get_text(msg).lower()).split() if len(w) > min_len ]
            count += 1
            if count % 250 == 0:
                await client.send_chat_action(message.chat.id, "playing")
                await response.edit(f"` → [{count}/{number}] ` Counting word occurrences...")
        count = Counter(words).most_common()
        from_who = f"(from **{get_username(user)}**)" if user else ""
        output = f"`→ {get_channel(group)}` {from_who}\n` → ` **{results}** most frequent words __(len > {min_len})__ in last **{number}** messages:\n"
        for i in range(results):
            output += f"`{i+1:02d}]{'-'*(results-i-1)}>` `{count[i][0]}` `({count[i][1]})`\n"
        await response.edit(output, parse_mode="markdown")
    except Exception as e:
        logger.exception("Error in .freq command")
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()
