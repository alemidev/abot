import random
import asyncio
import traceback

from telethon import events

import wikipedia
import italian_dictionary
from PyDictionary import PyDictionary

import requests

from util import set_offline, batchify
from util.globals import PREFIX
from util.permission import is_allowed

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
@events.register(events.NewMessage(pattern=r"{p}diz (?P<word>[^ ]+)".format(p=PREFIX)))
async def diz(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        arg = event.pattern_match.group("word")
        print(f" [ searching \"{arg}\" on it dictionary ]")
        # Use this to get only the meaning 
        res = italian_dictionary.get_definition(arg) 

        out = f"` → {res['lemma']} ` [ {' | '.join(res['sillabe'])} ]\n"
        out += f"```{', '.join(res['grammatica'])} - {res['pronuncia']}```\n\n"
        out += "\n\n".join(res['definizione'])
        for m in batchify(out, 4080):
            await event.message.reply(m)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e) if str(e) != "" else "Not found")
    await set_offline(event.client)

# Search on english dictionary
@events.register(events.NewMessage(pattern=r"{p}dic (?P<word>[^ ]+)".format(p=PREFIX)))
async def dic(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        arg = event.pattern_match.group('word')
        print(f" [ searching \"{arg}\" on eng dictionary ]")
        res = dictionary.meaning(arg)
        if res is None:
            return await event.message.reply("` → No match`")
        out = ""
        for k in res:
            out += f"`→ {k} : `"
            out += "\n * "
            out += "\n * ".join(res[k])
            out += "\n\n"
        for m in batchify(out, 4080):
            await event.message.reply(m)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Search on urban dictionary
@events.register(events.NewMessage(pattern=r"{p}ud (?P<word>[^ ]+)".format(p=PREFIX)))
async def urbandict(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        arg = event.pattern_match.group(1)
        print(f" [ searching \"{arg}\" on urban dictionary ]")
        res = ud_define(arg)
        if res is None:
            return await event.message.reply("`[!] → ` Not found")
        out = ""
        out += f"`→ {res['word']} [+{res['thumbs_up']}]: `\n"
        out += f"{res['definition']}\n\n"
        out += f"ex: __{res['example']}__\n\n"
        out += res['permalink']
        for m in batchify(out, 4080):
            await event.message.reply(m, link_preview=False)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Search on wikipedia
@events.register(events.NewMessage(pattern=r"{p}wiki (.*)".format(p=PREFIX)))
async def wiki(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        arg = event.pattern_match.group(1).replace(" ", "")
        print(f" [ searching \"{arg}\" on wikipedia ]")
        page = wikipedia.page(arg)
        out = f"` → {page.title}`\n"
        out += page.content[:750]
        out += f"... {page.url}"
        if len(page.images) > 0:
            try:
                await event.message.reply(out, link_preview=False,
                    file=page.images[0])
            except Exception as e:
                await event.message.reply(out)
        else:
            await event.message.reply(out, link_preview=False)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Let me google that for you
@events.register(events.NewMessage(pattern=r"{p}lmgtfy(?: |)(?P<query>.*)".format(p=PREFIX)))
async def lmgtfy(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        arg = event.pattern_match.group("query").replace(" ", "+")
        print(f" [ lmgtfy {arg} ]")
        if event.out:
            await event.message.edit(event.raw_text + f"\n` → ` http://letmegooglethat.com/?q={arg}")
        else:
            await event.message.reply(f"` → ` http://letmegooglethat.com/?q={arg}")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)


class SearchModules:
    def __init__(self, client):
        self.helptext = "`━━┫ SEARCH `\n"

        client.add_event_handler(urbandict)
        self.helptext += "`→ .ud <something> ` look up something on urban dictionary *\n"

        client.add_event_handler(dic)
        self.helptext += "`→ .dic <something> ` look up something on english dictionary *\n"

        client.add_event_handler(diz)
        self.helptext += "`→ .diz <something> ` look up something on italian dictionary *\n"

        client.add_event_handler(wiki)
        self.helptext += "`→ .wiki <something> ` search something on wikipedia *\n"

        client.add_event_handler(lmgtfy)
        self.helptext += "`→ .lmgtfy <something> ` make a lmgtfy link *\n"

        print(" [ Registered Search Modules ]")

    def helptext(self):
        return self.helptext
