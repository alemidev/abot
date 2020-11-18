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

async def edit_or_reply(message, text):
    if message.from_user is not None and message.from_user.is_self \
    and len(message.text + text) < 4090: 
        await message.edit(message.text + "\n" + text)
    else:
        for m in batchify(text, 4090):
            await message.reply(m)

def tokenize_json(text):
    res = re.subn(
        r'("[^\"]+"|[0-9.\-]+)',
        '``\g<1>``', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return tokenize_lines(text) # try to tokenize per line at least
    return "`" + res[0] + "`"

def tokenize_lines(text):
    res =  re.subn(r'(.+)', '`\g<1>`', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return "```" + text + "```"
    return res[0]
