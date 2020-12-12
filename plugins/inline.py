import traceback
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
FAKEPOLLS = {}

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
    global FAKEPOLLS
    if callback_query.data.startswith("FP|"):
        poll_id = callback_query.data.split("|")[2]
        answ = callback_query.data.split("|")[1]
        FAKEPOLLS[poll_id] += 1
        if answ == "correct":
            await client.answer_callback_query(
                callback_query.id,
                text="Correct!",
                show_alert=True
            )
        elif answ == "wrong":
            await client.answer_callback_query(
                callback_query.id,
                text="Wrong, lemme correct the answer for you",
                show_alert=True
            )
        try:
            await client.edit_inline_reply_markup(callback_query.inline_message_id, 
                            reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(f"{FAKEPOLLS[poll_id]} | Yes",
                                callback_data=f"FP|correct|{poll_id}"),
                            InlineKeyboardButton("0 | No",
                                callback_data=f"FP|wrong|{poll_id}")
                            ]]))
        except: # Message deleted? In FloodWait? Don't wait anyway it will cause inconsistency
            traceback.print_exc()
            pass
        return
    if callback_query.data in SPOILERS and "cantopen" in SPOILERS[callback_query.data] \
    and SPOILERS[callback_query.data]["cantopen"] == callback_query.from_user.id:
        return await client.answer_callback_query(
            callback_query.id,
            text="Sorry, but you can't view this secret!",
            show_alert=True
        )
        
    text = SPOILERS[callback_query.data]["text"] if callback_query.data in SPOILERS else "Spoiler expired"
    if callback_query.data in SPOILERS:
        SPOILERS[callback_query.data]["number"] +=1
    else:
        SPOILERS[callback_query.data]["number"] = 1
    n = SPOILERS[callback_query.data]["number"]
    await client.answer_callback_query(
        callback_query.id,
        text=text,
        show_alert=True
    )
    try:
        await client.edit_inline_reply_markup(callback_query.inline_message_id, 
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton(f"{n} | Show",
                                callback_data=str(hash(text))
                            )
                        ]]))
    except: # Message deleted? In FloodWait? Don't wait anyway it will cause inconsistency
        pass

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]hide(?: |)(?P<who>@[^ ]+|)(?: |)(?P<text>.*)"))
async def inline_spoiler(client, inline_query):
    global SPOILERS
    lgr.warning(f"Received SPOILER query from {get_username(inline_query.from_user)}")
    text = inline_query.matches[0]["text"]
    data = {"text" : text, "number": 0}
    who = inline_query.matches[0]["who"]
    userwhocantopen = ""
    if who != "":
        try:
            uid = (await client.get_users(who)).id
            data["cantopen"] = uid
            userwhocantopen = f"(hidden from {who})"
        except: #ignore
            pass
    SPOILERS[str(hash(text))] = data

    await inline_query.answer(
        results=[
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=f"send secret text {userwhocantopen}",
                        input_message_content=InputTextMessageContent(
                            f"{get_username(inline_query.from_user)} sent a --secret-- {userwhocantopen}"),
                        description=f"→ {text}",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Show",
                                callback_data=str(hash(text))
                            )
                        ]]))
        ],
        cache_time=1
    )

@alemiBot.on_inline_query(filters.regex(pattern="^[\\"+ "\\".join(alemiBot.prefixes) +"]fakepoll(?: |)(?P<text>.*)"))
async def inline_fakepoll(client, inline_query):
    global FAKEPOLLS
    lgr.warning(f"Received FAKEPOLL query from {get_username(inline_query.from_user)}")
    text = inline_query.matches[0]["text"]
    FAKEPOLLS[str(hash(text))] = 0

    await inline_query.answer(
        results=[
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=f"send fake poll",
                        input_message_content=InputTextMessageContent(
                            f"--{get_username(inline_query.from_user)} :-- {text}"),
                        description=f"→ ask \"{text}\"",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("0 | Yes",
                                callback_data=f"FP|correct|{str(hash(text))}"),
                            InlineKeyboardButton("0 | No",
                                callback_data=f"FP|wrong|{str(hash(text))}")
                        ]]))
        ],
        cache_time=1
    )

@alemiBot.on_inline_query()
async def inline_always(client, inline_query):
    lgr.warning(f"Received BASE query from {get_username(inline_query.from_user)}")
    q = inline_query.query
    results=[
                InlineQueryResultArticle(id=uuid4(),title=f"/hide",
                    description="Create a hidden message",
                    input_message_content=InputTextMessageContent(f"`[inline] → ` @{client.me.username} /hide [@who] <text>")),
                InlineQueryResultArticle(id=uuid4(),title=f"/fakepoll",
                    description="Create a fake poll",
                    input_message_content=InputTextMessageContent(f"`[inline] → ` @{client.me.username} /fakepoll <text>"))
    ]

    for k in CATEGORIES:
        for kk in CATEGORIES[k].HELP_ENTRIES:
            e = CATEGORIES[k].HELP_ENTRIES[kk]
            if q != "" and e.title.startswith(q):
                results.append(
                    InlineQueryResultArticle(
                        id=uuid4(),
                        title=e.title,
                        input_message_content=InputTextMessageContent(f"`→ {e.title} {e.args} `\n{e.longtext}"),
                        description=f"→ {e.shorttext}",
                    )
                )

    await inline_query.answer(
        switch_pm_text=f"→ Type command to get help",
        switch_pm_parameter="help",
        results=results,
        cache_time=5
    )
