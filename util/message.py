

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
