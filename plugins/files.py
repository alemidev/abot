import asyncio

from bot import alemiBot

from pyrogram import filters

from util.message import get_text
from plugins.help import HelpCategory

HELP = HelpCategory("FILES")

HELP.add_help("put", "save file to server",
                "reply to a media message or attach a media to this command to " +
                "store a file on the bot root folder.")
@alemiBot.on_message(filters.me & filters.command("put", list(alemiBot.prefixes)))
async def upload(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = message.reply_to_message
    if msg.media:
        try:
            fpath = await client.download_media(msg)
            await message.edit(get_text(message) + '\n` → ` saved file as {}'.format(fpath))
        except Exception as e:
            await message.edit(get_text(message) + "\n`[!] → ` " + str(e))
    else:
        await message.edit(get_text(message) + "\n`[!] → ` you need to attach or reply to a file, dummy")

HELP.add_help("get", "request a file from server",
                "will upload a file from server to this chat. The path can be " +
                "global.", args="<path>")
@alemiBot.on_message(filters.me & filters.command("get", list(alemiBot.prefixes)))
async def download(client, message):
    if len(message.command) < 2:
        return await message.edit(message.text.markdown + "\n`[!] → ` No filename provided")
    try:
        name = message.command[1]
        await client.send_document(message.chat.id, name, reply_to_message_id=message.message_id, caption=f'` → {name}`')
    except Exception as e:
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))
