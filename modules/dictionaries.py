import random
import asyncio

from telethon import events

import wikipedia
import italian_dictionary
from PyDictionary import PyDictionary

from util import can_react, set_offline, batchify

dictionary = PyDictionary()

# Search on italian dictionary
@events.register(events.NewMessage(pattern=r"\.diz (.*)"))
async def diz(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1)
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
@events.register(events.NewMessage(pattern=r"\.dic (.*)"))
async def dic(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1)
        print(f" [ searching \"{arg}\" on eng dictionary ]")
        # Use this to get only the meaning 
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

# Search on wikipedia
@events.register(events.NewMessage(pattern=r"\.wiki (.*)"))
async def wiki(event):
    if not can_react(event.chat_id):
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


class DictionaryModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(dic)
        self.helptext += "`→ .dic <something> ` look up something on english dictionary\n"

        client.add_event_handler(diz)
        self.helptext += "`→ .diz <something> ` look up something on italian dictionary\n"

        client.add_event_handler(wiki)
        self.helptext += "`→ .wiki <something> ` search something on wikipedia\n"

        print(" [ Registered Dictionary Modules ]")

    def helptext(self):
        return self.helptext
