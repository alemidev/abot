import asyncio
import secrets
import re
import os
import io
import json
import time
import traceback
import requests

from collections import Counter
from gtts import gTTS 
from pydub import AudioSegment
import speech_recognition as sr

from pyrogram import filters

from util.permission import is_allowed
from util.message import edit_or_reply, is_me, tokenize_json, get_text
from util.command import filterCommand

import translators as ts
from google_currency import convert
from unit_converter.converter import converts
from PIL import Image
import qrcode

from bot import alemiBot

from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()

HELP = HelpCategory("UTIL")

HELP.add_help(["convert", "conv"], "convert various units",
                "convert various measure units. Accepts many units, like " +
                "`.convert 52 °C °F` or `.convert 2.78 daN*mm^2 mN*µm^2`.",
                args="<val> <from> <to>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["convert", "conv"], list(alemiBot.prefixes)))
async def convert_cmd(client, message):
    if "cmd" not in message.command or len(message.command["cmd"] < 3):
        return await edit_or_reply(message, "`[!] → ` Not enough arguments")
    try:
        logger.info("Converting units")
        res = converts(message.command["cmd"][0] + " " + message.command["cmd"][1], message.command["cmd"][2])
        await edit_or_reply(message, f"` → ` {res} {message.command['cmd'][2]}")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["currency", "cconvert", "curr"], "convert across currencies",
                "convert various measure units. Accepts many currencies, like " +
                "`.convert 1 btc us`.",
                args="<val> <from> <to>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["currency", "cconvert", "curr"], list(alemiBot.prefixes)))
async def currency_convert_cmd(client, message):
    if "cmd" not in message.command or len(message.command["cmd"] < 3):
        return await edit_or_reply(message, "`[!] → ` Not enough arguments")
    try:
        logger.info("Converting currency")
        await client.send_chat_action(message.chat.id, "choose_contact")
        res = json.loads(convert(message.command["cmd"][1], message.command["cmd"][2], float(message.command["cmd"][0])))
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
@alemiBot.on_message(is_allowed & filterCommand(["countdown", "cd"], list(alemiBot.prefixes)), group=2)
async def countdown(client, message):
    if is_me(message):
        tgt_msg = message
    else:
        tgt_msg = await message.reply("` → `")
    end = time.time() + 5
    if "cmd" in message.command:
        try:
            end = time.time() + float(message.command["cmd"][0])
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
@alemiBot.on_message(is_allowed & filterCommand(["rand", "random", "roll"], list(alemiBot.prefixes), options={
    "batchsize" : ["-n"]
}))
async def rand_cmd(client, message):
    args = message.command
    try:
        res = []
        times = 1
        out = ""
        maxval = None
        if "arg" in args:
            pattern = r"(?P<batch>[0-9]*)d(?P<max>[0-9]+)"
            m = re.search(pattern, args["arg"])
            if m is not None:
                maxval = int(m["max"])
                if m["batch"] != "":
                    times = int(m["batch"])
            elif len(args["cmd"]) == 1 and args["cmd"][0].isnumeric():
                maxval = int(args["cmd"][0])
        if "batchsize" in args:
            times = int(args["batchsize"]) # overrule dice roller formatting
            
        if maxval is not None:
            logger.info(f"Rolling d{maxval}")
            for i in range(times):
                res.append(secrets.randbelow(maxval) + 1)
            if times > 1:
                out += f"`→ Rolled {times}d{maxval}` : **{sum(res)}**\n"
        elif "cmd" in args:
            logger.info(f"Rolling {args['cmd']}")
            for i in range(times):
                res.append(secrets.choice(args['cmd']))
            if times > 1: # This is kinda ugly but pretty handy
                res_count = Counter(res).most_common()
                max_times = res_count[0][1]
                out += "`→ Random choice ` **"
                for el in res_count:
                    if el[1] < max_times:
                        break
                    out += el[0] + " "
                out += "**\n"
        else:
            logger.info(f"Rolling binary")
            for i in range(times):
                res.append(secrets.randbelow(2))
            if times > 1:
                out += "`→ Binary " + "".join(str(x) for x in res) + "`\n"
                # this is a very ugly way to prevent the formatted print below
                res = []
                times = 0
        if times <= 20:
            for r in res:
                out += f"` → ` ** {r} **\n"
        else:
            out += f"` → ` [ " + " ".join(str(r) for r in res) + " ]"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["translate", "tran", "tr"], "translate to/from",
                "translate text from a language (autodetected if not specified, `-s`) to another " +
                "specified lang (defaults to eng, `-d`). Used engine can be specified with `-e` (available `google`, `deepl`, `bing`), " +
                "only `bing` works as of now and is the default. The lang codes must be 2 letter long (en, ja...)",
                args="[-s <src>] [-d <des>] [-e <engine>]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["translate", "tran", "tr"], list(alemiBot.prefixes), options={
    "src" : ["-s", "-src"],
    "dest" : ["-d", "-dest"],
    "engine" : ["-e", "-engine"]
}))
async def translate_cmd(client, message):
    args = message.command
    if "arg" not in args and message.reply_to_message is None:
        return await edit_or_reply(message, "`[!] → ` Nothing to translate")
    tr_options = {}
    # lmao I can probably pass **args directly
    if "src" in args:
        tr_options["from_language"] = args["src"]
    if "dest" in args:
        tr_options["to_language"] = args["dest"]
    engine = args["engine"] if "engine" in args else "bing"
    try:
        await client.send_chat_action(message.chat.id, "find_location")
        q = message.reply_to_message.text if message.reply_to_message is not None else args["arg"]
        logger.info(f"Translating {q}")
        out = "`[!] → ` Unknown engine"
        if engine == "google":
            out = "`[!] → ` As of now, this hangs forever, don't use yet!"
            # res = ts.google(q, **tr_options)
        elif engine == "deepl":
            out = ts.deepl(q, **tr_options)
        elif engine == "bing":
            out = "` → ` " + ts.bing(q, **tr_options)
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["qrcode", "qr"], "make qr code",
                "make a qr code with given text. Many parameters can be specified : size of specific boxes (`-box`), " +
                "image border (`-border`), qrcode size (`-size`). QR colors can be specified too: " +
                "background with `-b` and front color with `-f`",
                args="[-border <n>] [-size <n>] [-box <n>] [-b <color>] [-f <color>] <text>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["qrcode", "qr"], list(alemiBot.prefixes), options={
    "border" : ["-border"],
    "size" : ["-size"],
    "boxsize" : ["-box"],
    "back" : ["-b"],
    "front" : ["-f"]
}))
async def qrcode_cmd(client, message):
    args = message.command
    if "arg" not in args:
        return await edit_or_reply(message, "`[!] → ` No text given")
    text = args["arg"].replace("-delme", "") # just in case
    size = int(args["size"]) if "size" in args else None
    box_size = int(args["boxsize"]) if "boxsize" in args else 10
    border = int(args["border"]) if "border" in args else 4
    bg_color = args["back"] if "back" in args else "black"
    fg_color = args["front"] if "front" in args else "white"
    try:
        await client.send_chat_action(message.chat.id, "upload_photo")
        qr = qrcode.QRCode(
            version=size,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
        )
        qr.add_data(text)
        qr.make(fit=True)

        image = qr.make_image(fill_color=fg_color, back_color=bg_color)
        qr_io = io.BytesIO()
        qr_io.name = "qrcode.jpg"
        image.save(qr_io, "JPEG")
        qr_io.seek(0)
        await client.send_photo(message.chat.id, qr_io, reply_to_message_id=message.message_id)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["color"], "send solid color image",
                "create a solid color image and send it. Color can be given as hex or " +
                "by specifying each channel individally. Each channel can range from 0 to 256. ",
                args="( <hex> | <r> <g> <b> )", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["color"], list(alemiBot.prefixes)))
async def color_cmd(client, message):
    clr = None
    if "cmd" in message.command:
        if len(message.command["cmd"]) > 2:
            clr = tuple([int(k) for k in message.command["cmd"]][:3])
        else:
            clr = message.command["cmd"][0]
            if not clr.startswith("#"):
                clr = "#" + clr
    else:
        return await edit_or_reply(message, "`[!] → ` Not enough args given")
    try:
        await client.send_chat_action(message.chat.id, "upload_photo")
        image = Image.new("RGB", (200, 200), clr)
        color_io = io.BytesIO()
        color_io.name = "color.jpg"
        image.save(color_io, "JPEG")
        color_io.seek(0)
        await client.send_photo(message.chat.id, color_io, reply_to_message_id=message.message_id)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["voice"], "convert text to voice",
                "create a voice message using Google Text to Speech. By default, english will be " +
                "used as lang, but another one can be specified with `-l`. You can add `-slow` flag " +
                "to make the generated speech slower. If command comes from self, will delete original " +
                "message. TTS result will be converted to `.ogg`. You can skip this step and send as mp3 by " +
                "adding the `-mp3` flag. You can add the `-file` flag to make tts of a replied to or attached text file.",
                args="[-l <lang>] [-slow] [-mp3] <text>", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["voice"], list(alemiBot.prefixes), options={
    "lang" : ["-l", "-lang"]
}, flags=["-slow", "-mp3", "-file"]))
async def voice_cmd(client, message):
    text = ""
    opts = {}
    from_file = "-file" in message.command["flags"]
    if message.reply_to_message is not None:
        if from_file and message.reply_to_message.media:
            fpath = await client.download_media(message.reply_to_message)
            with open(fpath) as f:
                text = f.read()
            os.remove(fpath)
        else:
            text = get_text(message.reply_to_message)
    elif from_file and message.media:
        fpath = await client.download_media(message)
        with open(fpath) as f:
            text = f.read()
        os.remove(fpath)
    elif "arg" in message.command:
        text = re.sub(r"-delme(?: |)(?:[0-9]+|)", "", message.command["arg"])
    else:
        return await edit_or_reply(message, "`[!] → ` No text given")
    lang = message.command["lang"] if "lang" in message.command else "en"
    slow = "-slow" in message.command["flags"]
    try:
        if message.reply_to_message is not None:
            opts["reply_to_message_id"] = message.reply_to_message.message_id
        elif not is_me(message):
            opts["reply_to_message_id"] = message.message_id
        await client.send_chat_action(message.chat.id, "record_audio")
        gTTS(text=text, lang=lang, slow=slow).save("data/tts.mp3")
        if "-mp3" in message.command["flags"]:
            await client.send_audio(message.chat.id, "data/tts.mp3", **opts)
        else:
            AudioSegment.from_mp3("data/tts.mp3").export("data/tts.ogg", format="ogg", codec="libopus")
            await client.send_voice(message.chat.id, "data/tts.ogg", **opts)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["scribe"], "transcribes a voice message",
                "reply to a voice message to transcribe it. It uses Google Speech Recognition API. " +
                "It will work without a key but usage may get limited. You can try to [get a free key](http://www.chromium.org/developers/how-tos/api-keys) " +
                "and add it to your config under category [scribe] in a field named \"key\". You can specify speech " +
                "recognition language with `-l` (using `RFC5646` language tag format :  `en-US`, `it-IT`, ...)",
                args="[-l <lang>]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["scribe"], list(alemiBot.prefixes), options={
    "lang" : ["-l", "-lang"]
}))
async def transcribe_cmd(client, message):
    await client.send_chat_action(message.chat.id, "record_audio")
    msg = await edit_or_reply(message, "` → ` Working...")
    path = None
    lang = message.command["lang"] if "lang" in message.command else "en-US"
    if message.reply_to_message and message.reply_to_message.voice:
        path = await client.download_media(message.reply_to_message)
    elif message.voice:
        path = await client.download_media(message)
    else:
        return await edit_or_reply(message, "`[!] → ` No audio given")
    try:
        AudioSegment.from_ogg(path).export("data/voice.wav", format="wav")
        os.remove(path)
        voice = sr.AudioFile("data/voice.wav")
        with voice as source:
            audio = recognizer.record(source)
        out = "` → `" + recognizer.recognize_google(audio, language=lang,
                            key=alemiBot.config.get("scribe", "key", fallback=None))
        await edit_or_reply(msg, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(msg, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["ocr"], "read text in photos",
                "make a request to https://api.ocr.space/parse/image. The number of allowed queries " +
                "is limited, the result is not guaranteed and it requires an API key set up to work. " +
                "A language for the OCR can be specified with `-l`. You can request OCR.space overlay in response " +
                "with the `-overlay` flag. A media can be attached or replied to. Add the `-json` flag to get raw result.",
                args="[-l <lang>] [-overlay]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["ocr"], list(alemiBot.prefixes), options={
    "lang" : ["-l", "-lang"]
}, flags=["-overlay", "-json"]))
async def ocr_cmd(client, message):
    try:
        payload = {
            'isOverlayRequired': "-overlay" in message.command["flags"],
            'apikey': alemiBot.config.get("ocr", "apikey", fallback=""),
            'language': message.command["lang"] if "lang" in message.command else "eng"
        }
        if payload["apikey"] == "":
            return await edit_or_reply(message, "`[!] → ` No API Key set up")
        msg = message
        if message.reply_to_message is not None:
            msg = message.reply_to_message
        if msg.media:
            await client.send_chat_action(message.chat.id, "upload_photo")
            fpath = await client.download_media(msg, file_name="data/")
            with open(fpath, 'rb') as f:
                r = requests.post('https://api.ocr.space/parse/image', files={fpath: f}, data=payload)
            if "-json" in message.command["flags"]:
                raw = tokenize_json(json.dumps(json.loads(r.content.decode()), indent=2))
                await edit_or_reply(message, f"` → `\n{raw}")
            else:
                raw = json.loads(r.content.decode())
                out = ""
                for el in raw["ParsedResults"]:
                    out += el["ParsedText"]
                await edit_or_reply(message, f"` → ` {out}")
        else:
            return await edit_or_reply(message, "`[!] → ` No media given")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()
