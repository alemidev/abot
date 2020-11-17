import re

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

def tokenize_json(text):
    return "`" + re.sub(
        r'("[^\"]+"|[0-9.\-]+)',
        '``\g<1>``', text) + "`"

def tokenize_lines(text):
    asd =  re.sub(r'(.+)', '`\g<1>`', text)
    print(asd)
    return asd
