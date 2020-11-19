import subprocess
import io
import traceback

# handy libs to have for eval()
import datetime
import time
import requests
import sympy
import os
import re
import random
import math
import json

from bot import alemiBot

from pyrogram import filters

from util.parse import cleartermcolor
from util.message import tokenize_json, tokenize_lines
from plugins.help import HelpCategory

HELP = HelpCategory("EXECUTION")

HELP.add_help(["run", "r"], "run command on server",
                "runs a command on server. Shell will be from user running bot. " +
                "Every command starts in bot root folder.", args="<cmd>")
@alemiBot.on_message(filters.me & filters.command(["run", "r"], list(alemiBot.prefixes)))
async def runit(client, message):
    args = re.sub("^[\.\/](?:run|r)(?: |)", "", message.text)
    try:
        print(f" [ running command \"{args}\" ]")
        result = subprocess.run(args, shell=True, capture_output=True, timeout=60)
        output = cleartermcolor(result.stdout.decode())
        if len(args) + len(output) > 4080:
            await message.edit(f"```$ {args}\n → Output too long, sending as file```")
            out = io.BytesIO((f"$ {args}\n" + output).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out)
        else:
            await message.edit(tokenize_lines(f"$ {args}\n\n" + output))
    except Exception as e:
        traceback.print_exc()
        await message.edit(f"`$ {args}`\n`[!] → ` " + str(e))

HELP.add_help(["eval", "e"], "eval a python expression",
                "eval a python expression. No imports can be made nor variables can be " +
                "assigned. Some common libs are already imported.", args="<expr>")
@alemiBot.on_message(filters.me & filters.command(["eval", "e"], list(alemiBot.prefixes)))
async def evalit(client, message):
    args = re.sub("^[\.\/](?:eval|e)(?: |)", "", message.text)
    try:
        print(f" [ evaluating \"{args}\" ]")
        result = str(eval(args))
        if len(args) + len(result) > 4080:
            await message.edit(f"```>>> {args}\n → Output too long, sending as file```")
            out = io.BytesIO((f">>> {args}\n" + result).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out)
        else:
            await message.edit(tokenize_lines(f">>> {args}\n\n" + result))
    except Exception as e:
        traceback.print_exc()
        await message.edit(f"`>>> {args}`\n`[!] → ` " + str(e))
