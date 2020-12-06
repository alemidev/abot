from uuid import uuid4

from pyrogram import filters

from pyrogram.types import (
    InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)
from bot import alemiBot

from util.command import filterCommand
from util.user import get_username
from plugins.help import CATEGORIES

import logging
lgr = logging.getLogger(__name__)

SPOILERS = {}
PRESSES = {}

@alemiBot.on_message(filterCommand("start", list(alemiBot.prefixes)))
async def cmd_start(client, message):
    await message.reply("` → ` This bot provides inline help for my userbot commands.\n"
                        "It will also run (for everyone) the public commands, so you can try those!")

@alemiBot.on_message(filterCommand("make_botfather_list", list(alemiBot.prefixes)))
async def cmd_make_botfather_list(client, message):
    out = "help - [cmd] | get help for specific command or command list\n"
    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            out += f"{e.title} - {e.args} | {e.shorttext}\n"
    await message.reply(out, parse_mode='markdown')

@alemiBot.on_callback_query()
async def callback_spoiler(client, callback_query):
    global SPOILERS
    global PRESSES
    text = SPOILERS[callback_query.data] if callback_query.data in SPOILERS else "Spoiler expired"
    if callback_query.data in PRESSES:
        PRESSES[callback_query.data] +=1
    else:
        PRESSES[callback_query.data] = 1
    await client.answer_callback_query(
        callback_query.id,
        text=text,
        show_alert=True
    )
    await client.edit_inline_reply_markup(callback_query.inline_message_id, 
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(f"View spoiler [{PRESSES[callback_query.data]}]",
                                callback_data=str(hash(text))
                            )
                        ]]))

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]spoiler"))
async def inline_spoiler(client, inline_query):
    global SPOILERS
    global PRESSES
    lgr.warning(f"Received SPOILER query from {get_username(inline_query.from_user)}")
    text = inline_query.query[1:].replace("spoiler", "")
    SPOILERS[str(hash(text))] = text
    PRESSES[str(hash(text))] = 0

    await inline_query.answer(
        results=[
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=f"send spoiler",
                        input_message_content=InputTextMessageContent(
                            f"{get_username(inline_query.from_user)} sent a --spoiler--"),
                        description=f"→ {text}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("View spoiler [0]",
                                callback_data=str(hash(text))
                            )
                        ]]))
        ],
        cache_time=1
    )

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]run"))
async def inline_run(client, inline_query):
    lgr.warning(f"Received RUN query from {get_username(inline_query.from_user)}")
    results = []
    q = inline_query.query[1:].replace("run", "").strip()

    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            if q == "" or e.title.startswith(q):
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

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]help"))
async def inline_help(client, inline_query):
    lgr.warning(f"Received HELP query from {get_username(inline_query.from_user)}")
    q = inline_query.query[1:].replace("help", "").strip()
    results = []

    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            if q == "" or e.title.startswith(q):
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

@alemiBot.on_inline_query()
async def inline_always(client, inline_query):
    await inline_query.answer(
        results=[
                    InlineQueryResultArticle(id=uuid4(),title=f"/help",
                        description="Show help for userbot commands",
                        input_message_content=InputTextMessageContent(f"`[inline] → ` @{client.me.username} /help")),
                    InlineQueryResultArticle(id=uuid4(),title=f"/spoiler",
                        description="Create a spoiler text",
                        input_message_content=InputTextMessageContent(f"`[inline] → ` @{client.me.username} /spoiler")),
                    InlineQueryResultArticle(id=uuid4(),title=f"/run",
                        description="Send prefix and command",
                        input_message_content=InputTextMessageContent(f"`[inline] → ` @{client.me.username} /run")),
        ],
        cache_time=60
    )
