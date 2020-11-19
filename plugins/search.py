import asyncio
import traceback

from pyrogram import filters

from bot import alemiBot

import wikipedia
import italian_dictionary
from PyDictionary import PyDictionary

import requests

from util import batchify
from util.permission import is_allowed
from util.message import edit_or_reply
from plugins.help import HelpCategory

HELP = HelpCategory("SEARCH")

dictionary = PyDictionary()

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
                args="[word]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["diz", "dizionario"], list(alemiBot.prefixes)))
async def diz(_, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1]
        print(f" [ searching \"{arg}\" on it dictionary ]")
        # Use this to get only the meaning 
        res = italian_dictionary.get_definition(arg) 

        out = f"` → {res['lemma']} ` [ {' | '.join(res['sillabe'])} ]\n"
        out += f"```{', '.join(res['grammatica'])} - {res['pronuncia']}```\n\n"
        out += "\n\n".join(res['definizione'])
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e) if str(e) != "" else "Not found")

HELP.add_help(["dic", "dictionary"], "search in eng dict",
                "get definition from english dictionary of given word.",
                args="[word]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["dic", "dictionary"], list(alemiBot.prefixes)))
async def dic(_, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1]
        print(f" [ searching \"{arg}\" on eng dictionary ]")
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

HELP.add_help(["ud", "urban"], "search in urban dict",
                "get definition from urban dictionary of given word.",
                args="[word]", public=True)
@alemiBot.on_message(is_allowed & filters.command(["ud", "urban"], list(alemiBot.prefixes)))
async def urbandict(_, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1]
        print(f" [ searching \"{arg}\" on urban dictionary ]")
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

HELP.add_help("wiki", "search on wikipedia",
                "search on wikipedia, attaching initial text and a link.",
                args="[query]", public=True)
@alemiBot.on_message(is_allowed & filters.command("wiki", list(alemiBot.prefixes)))
async def wiki(_, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1]
        print(f" [ searching \"{arg}\" on wikipedia ]")
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

HELP.add_help("lmgtfy", "let me google that for you",
                "generates a `Let Me Google That For You` link.",
                args="[query]", public=True)
@alemiBot.on_message(is_allowed & filters.command("lmgtfy", list(alemiBot.prefixes)))
async def lmgtfy(_, message):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1].replace(" ", "+") # fuck it probably is already split at spaces, TODO
        print(f" [ lmgtfy {arg} ]")
        await edit_or_reply(message, f"` → ` http://letmegooglethat.com/?q={arg}")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help("location", "send a location",
                "send a location for specific latitude and longitude. Both has " +
                "to be given and are in range [-90, 90]", args="<lat> <long>", public=True)
@alemiBot.on_message(is_allowed & filters.command("location", list(alemiBot.prefixes)))
async def location_cmd(client, message):
    if len(message.command) < 3:
        return await edit_or_reply(message, "`[!] → ` Not enough args")
    latitude = float(message.command[1])
    longitude = float(message.command[2])
    if latitude > 90 or latitude < -90 or longitude > 90 or longitude < -90:
        return await edit_or_reply(message, "`[!] → ` Invalid coordinates")
    try:
        await client.send_location(message.chat.id, latitude, longitude)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
