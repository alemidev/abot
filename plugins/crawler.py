import asyncio
import re
import traceback

from pyrogram import filters

from util.chat import get_channel

from bot import alemiBot

import logging
logger = logging.getLogger(__name__)

@alemiBot.on_message(group=100)
async def join_all_groups(client, message):
    if message.entities is not None:
        try:
            for e in message.entities:
                if e.type == "mention":
                    mention = message.text[e.offset:e.offset+e.length]
                    chat = await client.get_chat(mention)
                    logger.warning("Joining " + get_channel(chat))
                    chat.join()
