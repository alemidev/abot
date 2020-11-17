import re
from . import batchify

async def get_channel(message):
    peer = await message.get_input_peer()
    if peer is None:
        return None
    chan = await message.client.get_entity(peer)
    if hasattr(chan, "title"):
        return chan
    if message.out:
        return chan
    else:
        return await message.client.get_entity(
                    await message.get_input_sender())

async def edit_or_reply(event, message):
    if event.out and len(event.raw_text + message) < 4090: 
        await event.message.edit(event.raw_text + "\n" + message)
    else:
        for m in batchify(message, 4080):
            await event.message.reply(m)

def tokenize_json(text):
    res = re.subn(
        r'("[^\"]+"|[0-9.\-]+)',
        '``\g<1>``', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return "```" + text + "```"
    return "`" + res[0] + "`"

def tokenize_lines(text):
    res =  re.subn(r'(.+)', '`\g<1>`', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return "```" + text + "```"
    return res[0]
