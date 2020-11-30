import asyncio
import secrets
import re
import json
import time
import traceback

from collections import Counter

from pyrogram import filters

from util.permission import is_allowed
from util.message import edit_or_reply, is_me
from util.parse import newFilterCommand

from googletrans import Translator
from google_currency import convert
from unit_converter.converter import converts
import qrcode

from bot import alemiBot

from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

translator = Translator()

HELP = HelpCategory("UTIL")

HELP.add_help(["convert", "conv"], "convert various units",
                "convert various measure units. Accepts many units, like " +
                "`.convert 52 °C °F` or `.convert 2.78 daN*mm^2 mN*µm^2`.",
                args="<val> <from> <to>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["convert", "conv"], list(alemiBot.prefixes)))
async def convert_cmd(client, message):
    if len(message.command) < 4:
        return await edit_or_reply(message, "`[!] → ` Not enough arguments")
    try:
        logger.info("Converting units")
        res = converts(message.command[1] + " " + message.command[2], message.command[3])
        await edit_or_reply(message, f"` → ` {res} {message.command[3]}")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["currency", "cconvert", "curr"], "convert across currencies",
                "convert various measure units. Accepts many currencies, like " +
                "`.convert 1 btc us`.",
                args="<val> <from> <to>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["currency", "cconvert", "curr"], list(alemiBot.prefixes)))
async def currency_convert_cmd(client, message):
    if len(message.command) < 4:
        return await edit_or_reply(message, "`[!] → ` Not enough arguments")
    try:
        logger.info("Converting currency")
        await client.send_chat_action(message.chat.id, "choose_contact")
        res = json.loads(convert(message.command[2], message.command[3], float(message.command[1])))
        await edit_or_reply(message, f"` → ` {res['amount']} {res['to']}")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

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
                args="[<time>]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["countdown", "cd"], list(alemiBot.prefixes)), group=2)
async def countdown(client, message):
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
    logger.info(f"Countdown")
    while time.time() < end:
        curr = msg.format(time.time() - end)
        if curr != last: # with fast counting down at the end it may try to edit with same value
            await tgt_msg.edit(msg.format(time.time() - end))
            last = curr
        await asyncio.sleep(interval(end - time.time()))
    await tgt_msg.edit(msg.format(0))
    await client.set_offline()

HELP.add_help(["rand", "random", "roll"], "get random choices",
                "this can be used as a dice roller (`.roll 3d6`). If a list of choices is given, a random one " +
                "will be chosen from that. If a number is given, it will choose a value from 1 to <n>, both included. " +
                "You can specify how many extractions to make", args="[-n <n>] [choices] | [n]d<max>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["rand", "random", "roll"], list(alemiBot.prefixes)) & filters.regex(pattern=
    r"^.(?:random|rand|roll)(?: |)(?:(?:(?P<num>[0-9]+|)d(?P<max>[0-9]+))|(?:(?P<batch>-n [0-9]+|)(?: |)(?P<values>.*)))"
)) # this is better with a regex because allows the "dice roller" format, aka 3d6
async def rand_cmd(client, message):
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
            logger.info(f"Rolling d{maxval}")
            for i in range(times):
                res.append(secrets.randbelow(maxval) + 1)
            if times > 1:
                out += f"`→ Rolled {times}d{maxval}` : **{sum(res)}**\n"
        elif args["values"] != None and args["values"] != "":
            choices = args["values"].split(" ")
            logger.info(f"Rolling {choices}")
            for i in range(times):
                res.append(secrets.choice(choices))
            res_count = Counter(res)
            if times > 1:
                out += "`→ Random choice ` **" + res_count.most_common(1)[0][0] + "**\n"
        else:
            choices = [ 1, 0 ]
            logger.info(f"Rolling {choices}")
            for i in range(times):
                res.append(secrets.choice(choices))
            if times > 1:
                out += "` → Binary " + "".join(str(x) for x in res) + "`\n"
                res = [] # so it won't do the thing below
        if times <= 20:
            for r in res:
                out += f"` → ` **{r}**\n"
        else:
            out += f"` → ` [ " + " ".join(str(r) for r in res) + "]"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["translate", "tran", "tr"], "translate to/from",
                "translate text from a language (autodetected if not specified, `-s`) to another " +
                "specified lang (defaults to eng, `-d`). It will show the confidence for detected lang. This " +
                "uses google translate. The lang codes must be 2 letter long (en, ja...)", args="[-s <src>] [-d <des>]", public=True)
@alemiBot.on_message(is_allowed & newFilterCommand(["translate", "tran", "tr"], list(alemiBot.prefixes), options={
    "src" : ["-s", "-src"],
    "dest" : ["-d", "-dest"]
}))
async def translate_cmd(client, message):
    args = message.command
    if "arg" not in args:
        return await edit_or_reply(message, "`[!] → ` Nothing to translate")
    tr_options = {}
    # lmao I can probably pass **args directly
    if "src" in args:
        tr_options["src"] = args["src"]
    if "dest" in args:
        tr_options["dest"] = args["dest"]
    try:
        await client.send_chat_action(message.chat.id, "find_location")
        q = args["arg"]
        logger.info(f"Translating {q}")
        res = translator.translate(q, **tr_options)
        out = f"`[{res.extra_data['confidence']:.2f}] → ` {res.text}"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["qrcode", "qr"], "make qr code",
                "make a qr code with given text. Many parameters can be specified : image size (`-s`), " +
                "image border (`-border`), qrcode version (`-version`). QR colors can be specified too: " +
                "background with `-b` and front color with `-f`",
                args="[-border <n>] [-s <n>] [-b <color>] [-f <color>] <text>", public=True)
@alemiBot.on_message(is_allowed & newFilterCommand(["qrcode", "qr"], list(alemiBot.prefixes), options={
    "border" : ["-border"],
    "size" : ["-s"],
    "back" : ["-b"],
    "front" : ["-f"]
}))
async def qrcode_cmd(client, message):
    args = message.command
    if "arg" not in args:
        return await edit_or_reply(message, "`[!] → ` No text given")
    text = args["text"]
    size = int(args["size"]) if "size" in args else 10
    border = int(args["border"]) if "border" in args else 4
    bg_color = args["back"] if "back" in args else "black"
    fg_color = args["front"] if "front" in args else "white"
    try:
        await client.send_chat_action(message.chat.id, "upload_photo")
        qr = qrcode.QRCode(
            version=None, # auto determine best size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        imgage = qr.make_image(fill_color=bg_color, back_color=fg_color)
        image = qrcode.make(text)
        fried_io = io.BytesIO()
        fried_io.name = "qrcode.jpg"
        image.save(fried_io, "JPEG")
        fried_io.seek(0)
        await client.send_photo(message.chat.id, fried_io, reply_to_message_id=message.message_id)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()
