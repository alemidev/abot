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

async def attempt_joining(mention):
    global JOINED
    if mention in JOINED:
        return
    try:    
        await client.join_chat(mention)
        JOINED.add(mention)
        logger.warning("Joined " + mention)
    except BadRequest as e:
        JOINED.add(mention) # This isn't a channel/group anyway
        logger.warn("Failed to join " + mention + ", (already a member or not a channel/group)")
    except FloodWait as e:
        logger.warn("Failed to join " + mention + ": " + str(e))
        await client.send_message("me", mention + " - couldn't wait because in FloodWait")

@alemiBot.on_message(group=100)
async def join_all_groups(client, message):
    try:
        if message.forward_from_chat is not None:
            await attempt_joining(message.forward_from_chat.id)
        if message.entities is not None:
            for e in message.entities:
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
                await attempt_joining(mention)
    except Exception as e: # Basically ignore
        logger.warn(str(e))
                
