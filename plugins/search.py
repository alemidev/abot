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

# Search on italian dictionary
@alemiBot.on_message(is_allowed & filters.command(["diz", "dizionario"], prefixes="."))
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
        await edit_or_reply(message, "`[!] → ` " + str(e) if str(e) != "" else "Not found")

# Search on english dictionary
@alemiBot.on_message(is_allowed & filters.command(["dic", "dictionary"], prefixes="."))
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
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Search on urban dictionary
@alemiBot.on_message(is_allowed & filters.command(["ud", "urban"], prefixes="."))
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
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Search on wikipedia
@alemiBot.on_message(is_allowed & filters.command("wiki", prefixes="."))
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
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Let me google that for you
@alemiBot.on_message(is_allowed & filters.command("lmgtfy", prefixes="."))
async def lmgtfy(event):
    if len(message.command) < 2:
        return await edit_or_reply(message, "`[!] → ` No query given")
    try:
        arg = message.command[1].replace(" ", "+") # fuck it probably is already split at spaces, TODO
        print(f" [ lmgtfy {arg} ]")
        await edit_or_reply(message, f"` → ` http://letmegooglethat.com/?q={arg}")
    except Exception as e:
        await edit_or_reply(message, "`[!] → ` " + str(e))

# class SearchModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ SEARCH `\n"
# 
#         client.add_event_handler(urbandict)
#         self.helptext += "`→ .ud <something> ` look up something on urban dictionary *\n"
# 
#         client.add_event_handler(dic)
#         self.helptext += "`→ .dic <something> ` look up something on english dictionary *\n"
# 
#         client.add_event_handler(diz)
#         self.helptext += "`→ .diz <something> ` look up something on italian dictionary *\n"
# 
#         client.add_event_handler(wiki)
#         self.helptext += "`→ .wiki <something> ` search something on wikipedia *\n"
# 
#         client.add_event_handler(lmgtfy)
#         self.helptext += "`→ .lmgtfy <something> ` make a lmgtfy link *\n"
# 
#         print(" [ Registered Search Modules ]")
# 
#     def helptext(self):
#         return self.helptext
