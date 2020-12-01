import asyncio

from bot import alemiBot

from pyrogram import filters

from util.parse import newFilterCommand
from util.message import get_text
from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

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
            logger.info("Downloading media")
            fpath = await client.download_media(msg)
            await message.edit(get_text(message) + '\n` → ` saved file as {}'.format(fpath))
        except Exception as e:
            await message.edit(get_text(message) + "\n`[!] → ` " + str(e))
    else:
        await message.edit(get_text(message) + "\n`[!] → ` you need to attach or reply to a file, dummy")

HELP.add_help("get", "request a file from server",
                "will upload a file from server to this chat. The path can be " +
                "global. Use flag `-log` to automatically include `/data/scraped_media`.",
                args="[-log] <path>")
@alemiBot.on_message(filters.me & newFilterCommand("get", list(alemiBot.prefixes), flags=["-log"]))
async def download(client, message):
    if "cmd" not in message.command:
        return await message.edit(message.text.markdown + "\n`[!] → ` No filename provided")
    try:
        logger.info("Uploading media")
        await client.send_chat_action(message.chat.id, "upload_document")
        name = message.command["cmd"][0]
        if "-log" in message.command["flags"]:
            name = "data/scraped_media/" + name
        await client.send_document(message.chat.id, name, reply_to_message_id=message.message_id, caption=f'` → {name}`')
    except Exception as e:
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
