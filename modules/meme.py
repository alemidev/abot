import random
import asyncio
import os

from telethon import events

from util import can_react, set_offline, batchify

# Get list of memes
@events.register(events.NewMessage(pattern=r"\.listmeme"))
async def memelist(event):
    if not event.out or not can_react(event.chat_id):
        return
    try:
        print(" [ getting meme list ]")
        memes = os.listdir("data/memes")
        memes.sort()
        out = f"` → ` **Meme list** ({len(memes)} total) :\n[ "
        out += ", ".join(memes)
        out += "]"
        for m in batchify(out, 4090):
            await event.message.reply(m)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Get specific meme
@events.register(events.NewMessage(pattern=r"\.smeme (.*)"))
async def memespecific(event):
    if not event.out or not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1).split(" ")[0] # just in case don't allow spaces
        fname = [s for s in os.listdir("data/memes") if arg in s.lower()] # I can't decide if this is nice or horrible
        if len(fname) > 0:
            fname = fname[0]
            print(f" [ getting specific meme : \"{fname}\" ]")
            await event.message.reply('` → {}`'.format(fname), file=("data/memes/" + fname))
        else:
            await event.message.reply(f"`[!] → ` no meme named {arg}")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Get random meme from memes folder
@events.register(events.NewMessage(pattern=r"\.meme"))
async def meme(event):
    if not can_react(event.chat_id):
        return
    try:
        fname = random.choice(os.listdir("data/memes"))
        print(f" [ getting random meme : \"{fname}\" ]")
        await event.message.reply('` → {}`'.format(fname), file=("data/memes/" + fname))
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Save a meme
@events.register(events.NewMessage(pattern=r"\.steal (.*)"))
async def steal(event):
    if not event.out or not can_react(event.chat_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        arg = event.pattern_match.group(1).split(" ")[0] # just in case don't allow spaces
        print(f" [ stealing meme as \"{arg}\" ]")
        try:
            fname = await event.client.download_media(message=msg, file="data/memes/"+arg)
            await event.message.reply('` → ` saved meme as {}'.format(fname.replace("data/memes/", "")))
        except Exception as e:
            await event.message.reply("`[!] → ` " + str(e))
    else:
        await event.message.reply("`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

class MemeModules:
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(memelist)
        self.helptext += "`→ .listmeme ` print a list of memes in collection *\n"

        client.add_event_handler(memespecific)
        self.helptext += "`→ .smeme <name> ` get specific meme *\n"

        client.add_event_handler(meme)
        self.helptext += "`→ .meme ` get a random meme from collection\n"

        client.add_event_handler(steal)
        self.helptext += "`→ .steal <name> ` add meme to collection *\n"

        print(" [ Registered Meme Modules ]")
