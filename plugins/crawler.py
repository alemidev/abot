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
        for e in message.entities:
            try:
                if e.type == "mention" or e.type == "url":
                    mention = message.text[e.offset:e.offset+e.length]
                    logger.warning("Joining " + mention)
                    await client.join_chat(mention)
            except Exception as e:
                logger.warn(str(e))
                
