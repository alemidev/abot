import re
from . import batchify

def get_text(message):
    if message.text is None:
        if message.caption is None:
            return message.caption
        else:
            return ""
    else:
        return message.text

async def edit_or_reply(message, text):
    if message.from_user is not None and message.from_user.is_self \
    and len(message.text + text) < 4090: 
        await message.edit(message.text + "\n" + text)
    else:
        for m in batchify(text, 4090):
            await message.reply(m)

def tokenize_json(text):
    res = re.subn(
        r'("[^\"]+"|[0-9.\-]+)',
        '``\g<1>``', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return tokenize_lines(text) # try to tokenize per line at least
    return "`" + res[0] + "`"

def tokenize_lines(text):
    res =  re.subn(r'(.+)', '`\g<1>`', text)
    if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
        return "```" + text + "```"
    return res[0]
