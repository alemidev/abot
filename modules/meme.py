import random
import asyncio
import os
import traceback

from telethon import events

from util import can_react, set_offline, batchify

# Get random meme from memes folder
@events.register(events.NewMessage(
    pattern=r"^[\.\/]meme(?: |$)(?P<list>-list|-l|)(?: |$ |)(?P<name>[^ ]*)"))
async def getmeme(event):
    if not can_react(event.chat_id):
        return
    try:
        args = event.pattern_match.groupdict()
        if "list" in args and args["list"] in { "-l", "-list" }:
            print(" [ getting meme list ]")
            memes = os.listdir("data/memes")
            memes.sort()
            out = f"` → ` **Meme list** ({len(memes)} total) :\n[ "
            out += ", ".join(memes)
            out += "]"
            for m in batchify(out, 4090):
                await event.message.reply(m)
        elif "name" in args and args["name"] != "":
            print(f" [ getting specific meme : \"{args['name']}\" ]")
            memes = [ s for s in os.listdir("data/memes")      # I can't decide if this
                        if s.lower().startswith(args["name"])] #  is nice or horrible
            if len(memes) > 0:
                fname = memes[0]
                print(f" [ getting specific meme : \"{fname}\" ]")
                await event.message.reply('` → ` **{}**'.format(fname), file=("data/memes/" + fname))
            else:
                await event.message.reply(f"`[!] → ` no meme named {args['name']}")
        else: 
            fname = random.choice(os.listdir("data/memes"))
            print(f" [ getting random meme : \"{fname}\" ]")
            await event.message.reply('` → Random meme : ` **{}**'.format(fname), file=("data/memes/" + fname))
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Save a meme
@events.register(events.NewMessage(pattern=r"^[\.\/]steal (?P<name>[^ ]*)", outgoing=True))
async def steal(event):
    if not can_react(event.chat_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        arg = event.pattern_match.group("name")
        if arg == "":
            return await event.message.edit(event.raw_text + "\n`[!] → ` you need to provide a name")
        print(f" [ stealing meme as \"{arg}\" ]")
        try:
            fname = await event.client.download_media(message=msg, file="data/memes/"+arg)
            await event.message.edit(event.raw_text +
                '\n` → ` saved meme as {}'.format(fname.replace("data/memes/", "")))
        except Exception as e:
            await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    else:
        await event.message.edit(event.raw_text + 
                "\n`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

class MemeModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(getmeme)
        self.helptext += "`→ .meme [-list] [name]` get a meme\n"

        client.add_event_handler(steal)
        self.helptext += "`→ .steal [name] ` add meme to collection *\n"

        print(" [ Registered Meme Modules ]")
