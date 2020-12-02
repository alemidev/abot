from uuid import uuid4

from pyrogram import filters

from pyrogram.types import (
    InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)
from bot import alemiBot

from util.user import get_username
from plugins.help import CATEGORIES

import logging
lgr = logging.getLogger(__name__)


@alemiBot.on_message(filters.command("start", list(alemiBot.prefixes)))
async def cmd_start(client, message):
    await message.reply("` → ` This bot provides inline help for my userbot commands.\n"
                        "It will also run (for everyone) the public commands, so you can try those!")

@alemiBot.on_message(filters.command("make_botfather_list", list(alemiBot.prefixes)))
async def cmd_start(client, message):
    out = ""
    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            out += f"{e.title} - {e.args} | {e.shorttext}\n"
    await message.reply(out)

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]"), group=0)
async def inline_run(client, inline_query):
    lgr.warning(f"Received RUN query from {get_username(inline_query.from_user)}")
    results = []

    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            if inline_query.query[1:] == "" or e.title.startswith(inline_query.query[1:]):
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=f"run .{e.title}",
                        input_message_content=InputTextMessageContent(f"/{e.title}"),
                        description=f"→ {e.args}",
                    )
                )

    await inline_query.answer(
        results=results,
        cache_time=1
    )

@alemiBot.on_inline_query(group=2)
async def inline_help(client, inline_query):
    lgr.warning(f"Received HELP query from {get_username(inline_query.from_user)}")
    results = []

    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            if inline_query.query == "" or e.title.startswith(inline_query.query):
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=e.title,
                        input_message_content=InputTextMessageContent(f"`→ {e.title} {e.args} `\n{e.longtext}"),
                        description=f"→ {e.shorttext}",
                    )
                )

    await inline_query.answer(
        results=results,
        cache_time=1
    )