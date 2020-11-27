import re
import asyncio
import traceback

from pyrogram import filters

from bot import alemiBot

import wikipedia
import italian_dictionary
from PyDictionary import PyDictionary
from geopy.geocoders import Nominatim

import requests

from util import batchify
from util.permission import is_allowed
from util.message import edit_or_reply
from util.parse import newFilterCommand

from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

HELP = HelpCategory("SEARCH")

dictionary = PyDictionary()
geolocator = Nominatim(user_agent="telegram-client")

def ud_define(word):
    try:
        r = requests.get("http://api.urbandictionary.com/v0/define?term=" + word.capitalize(), timeout=10)
        if r.status_code == 200:
            best = 0
            match = None
            for el in r.json()["list"]:
                if el["thumbs_up"] > best:
                    best = el["thumbs_up"]
                    match = el
            return match
        else:
            return None
    except Exception as e:
        traceback.print_exc()
        return None

HELP.add_help(["diz", "dizionario"], "search in ita dict",
                "get definition from italian dictionary of given word.",
                args="<word>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["diz", "dizionario"], list(alemiBot.prefixes)))
async def diz(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        arg = message.command[1]
        logger.info(f"Searching \"{arg}\" on it dictionary")
        # Use this to get only the meaning 
        res = italian_dictionary.get_definition(arg) 

        out = f"` → {res['lemma']} ` [ {' | '.join(res['sillabe'])} ]\n"
        out += f"```{', '.join(res['grammatica'])} - {res['pronuncia']}```\n\n"
        out += "\n\n".join(res['definizione'])
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e) if str(e) != "" else "Not found")
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["dic", "dictionary"], "search in eng dict",
                "get definition from english dictionary of given word.",
                args="<word>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["dic", "dictionary"], list(alemiBot.prefixes)))
async def dic(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        arg = message.command[1]
        logger.info(f"Searching \"{arg}\" on eng dictionary")
        res = dictionary.meaning(arg)
        if res is None:
            return await edit_or_reply(message, "` → No match`")
        out = ""
        for k in res:
            out += f"`→ {k} : `"
            out += "\n * "
            out += "\n * ".join(res[k])
            out += "\n\n"
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help(["ud", "urban"], "search in urban dict",
                "get definition from urban dictionary of given word.",
                args="<word>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["ud", "urban"], list(alemiBot.prefixes)))
async def urbandict(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        arg = message.command[1]
        logger.info(f"Searching \"{arg}\" on urban dictionary")
        res = ud_define(arg)
        if res is None:
            return await edit_or_reply(message, "`[!] → ` Not found")
        out = ""
        out += f"`→ {res['word']} [+{res['thumbs_up']}]: `\n"
        out += f"{res['definition']}\n\n"
        out += f"ex: __{res['example']}__\n\n"
        out += res['permalink']
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help("wiki", "search on wikipedia",
                "search on wikipedia, attaching initial text and a link.",
                args="<query>", public=True)
@alemiBot.on_message(is_allowed & filters.command("wiki", list(alemiBot.prefixes)))
async def wiki(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        arg = " ".join(message.command[1:])
        logger.info(f"Searching \"{arg}\" on wikipedia")
        page = wikipedia.page(arg)
        out = f"` → {page.title}`\n"
        out += page.content[:750]
        out += f"... {page.url}"
        await edit_or_reply(message, out)
        # if len(page.images) > 0:
        #     try:
        #         await event.message.reply(out, link_preview=False,
        #             file=page.images[0])
        #     except Exception as e:
        #         await event.message.reply(out)
        # else:
        #     await event.message.reply(out, link_preview=False)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()

HELP.add_help("lmgtfy", "let me google that for you",
                "generates a `Let Me Google That For You` link.",
                args="<query>", public=True)
@alemiBot.on_message(is_allowed & filters.command("lmgtfy", list(alemiBot.prefixes)))
async def lmgtfy(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = "+".join(message.command[1:])
        logger.info(f"lmgtfy {arg}")
        await edit_or_reply(message, f"` → ` http://letmegooglethat.com/?q={arg}")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["loc", "location"], "send a location",
                "send a location for specific latitude and longitude. Both has " +
                "to be given and are in range [-90, 90]. If a title is given with the `-t` " +
                "option, the location will be sent as venue.", args="[-t <title>] (<lat> <long> | <loc>)", public=True)
@alemiBot.on_message(is_allowed & newFilterCommand(["loc", "location"], list(alemiBot.prefixes), options={
    "title" : ["-t"]
}))
async def location_cmd(client, message):
    args = message.command
    latitude = 0.0
    longitude = 0.0
    logger.info("Getting a location")
    if "arg" in args:
        try:
            coords = args["arg"].split(" ", 2)
            latitude = float(coords[0])
            longitude = float(coords[1])
        except (ValueError, IndexError):
            await client.send_chat_action(message.chat.id, "find_location")
            location = geolocator.geocode(args["arg"])
            await client.send_chat_action(message.chat.id, "cancel")
            if location is None:
                return await edit_or_reply(message, "`[!] → ` Not found")
            latitude = location.latitude
            longitude = location.longitude
    if latitude > 90 or latitude < -90 or longitude > 90 or longitude < -90:
        return await edit_or_reply(message, "`[!] → ` Invalid coordinates")
    try:
        if "title" in args:
            adr = (args["arg"] if "arg" in args else f"{latitude:.2f} {longitude:.2f}")
            await client.send_venue(message.chat.id, latitude, longitude,
                                        title=args["title"], address=adr)
        else:
            await client.send_location(message.chat.id, latitude, longitude)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

WTTR_STRING = "`→ {loc} `\n` → `**{desc}**\n` → ` {mintemp:.0f}C - {maxtemp:.0f}C `|` **{hum}%** humidity\n" + \
              "` → ` pressure **{press}hPa** `|` wind **{wspd}m/s**\n` → ` **{vis}m** visibility (__{cld}% clouded__)"

HELP.add_help(["weather", "wttr"], "get weather of location",
                "makes a request to wttr.in for provided location. Props to https://github.com/chubin/wttr.in " +
                "for awesome site, remember you can `curl wttr.in` in terminal.",
                # "searches OpenWeatherMap for specified location. To make queries to OpenWeatherMap " +
                # "an API key is necessary, thus registering to OpenWeatherMap. This is super early and shows very little.",
                args="<location>", public=True)
@alemiBot.on_message(is_allowed & filters.command(["weather", "wttr"], list(alemiBot.prefixes)))
async def weather_cmd(client, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` Not enough arguments")
    # APIKEY = alemiBot.config.get("weather", "apikey", fallback="")
    # if APIKEY == "":
    #     return await edit_or_reply(message, "`[!] → ` No APIKEY provided in config")
    try:
        logger.info("curl wttr.in")
        await client.send_chat_action(message.chat.id, "find_location")
        q = " ".join(message.command[1:])
        r = requests.get(f"https://wttr.in/{q}?mnTC0&lang=en")
        await edit_or_reply(message, "<code> → " + r.text + "</code>", parse_mode="html")
        # # Why bother with OpenWeatherMap?
        # r = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={q}&APPID={APIKEY}').json()
        # if r["cod"] != 200:
        #     return await edit_or_reply(message, "`[!] → ` Query failed")
        # await edit_or_reply(message, WTTR_STRING.format(loc=r["name"], desc=r["weather"][0]["description"],
        #                                                 mintemp=r["main"]["temp_min"] - 272.15,
        #                                                 maxtemp=r["main"]["temp_max"] - 272.15,
        #                                                 hum=r["main"]["humidity"], press=r["main"]["pressure"],
        #                                                 wspd=r["wind"]["speed"], vis=r["visibility"], cld=r["clouds"]["all"]))
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()
