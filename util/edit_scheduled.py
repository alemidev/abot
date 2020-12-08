import asyncio

from pyrogram.raw.functions.messages import DeleteScheduledMessages, GetScheduledHistory, SendScheduledMessages
from pyrogram.raw.types import InputPeerChannel, InputPeerUser

async def edit_scheduled(client, message, text):
    opts = {}
    if message.reply_to_message:
        opts["reply_to_message_id"] = message.reply_to_message.message_id
    peer = await client.resolve_peer(message.chat.id)
    await message._client.send(DeleteScheduledMessages(peer, message.message_id))
    return await message._client.send_message(message.chat.id, message.text.markdown, **opts, schedule_date=message.date)