import asyncio
import re
import traceback

from pyrogram import filters
from pyrogram.errors import FloodWait, BadRequest

from util.chat import get_channel

from bot import alemiBot

import logging
logger = logging.getLogger(__name__)

JOINED = set()

@alemiBot.on_message(group=100)
async def join_all_groups(client, message):
    global JOINED
    if message.entities is not None:
        for e in message.entities:
            try:
                if e.type == "mention":
                    mention = message.text[e.offset:e.offset+e.length]
                elif e.type == "text_link":
                    mention = e.url
                    if not mention.startswith("https://t.me/joinchat"):
                        continue
                elif e.type == "url":
                    mention = message.text[e.offset:e.offset+e.length]
                    if not mention.startswith("https://t.me/joinchat"):
                        continue
                else:
                    continue

                if mention in JOINED:
                    continue
                try:    
                    logger.warning("Joining " + mention)
                    await client.join_chat(mention)
                except BadRequest as e:
                    logger.warn(str(e))
                finally:
                    JOINED.add(mention)
            except Exception as e:
                logger.warn(str(e))
                
