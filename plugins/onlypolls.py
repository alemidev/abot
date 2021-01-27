from pyrogram import filters

from bot import alemiBot

@alemiBot.on_message(filters.chat(int(alemiBot.config.get("onlypolls", "chatid", fallback="0"))), group=420)
async def is_it_a_poll(client, message):
    if not message.poll or not message.poll.is_anonymous:
        await message.delete()
