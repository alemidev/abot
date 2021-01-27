import asyncio

from pyrogram import filters

from bot import alemiBot

@alemiBot.on_message(filters.regex(pattern=".*@admin.*"), group=112)
async def sei_uno_sbirro(client, message):
    msg = await message.reply("amico delle guardie")
    await asyncio.sleep(10)
    await msg.delete()
