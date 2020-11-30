from uuid import uuid4

from pyrogram import filters

from pyrogram.types import (
    InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
)
from bot import alemiBot

from plugins.help import CATEGORIES

@alemiBot.on_inline_query()
async def inline_help(client, inline_query):
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
