import asyncio
import io
import re
import traceback
import logging
import sys
import inspect

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

from util.command import filterCommand
from util.parse import cleartermcolor
from util.message import tokenize_json, tokenize_lines, is_me, edit_or_reply
from util.serialization import convert_to_dict
from util.permission import is_superuser
from plugins.help import HelpCategory

logger = logging.getLogger(__name__)

class GlobalThings():
    def __str__(self):
        return str(convert_to_dict(self))

GLOBALS = GlobalThings()

class stdoutWrapper(): 
    def __init__(self):
        self.buffer = io.StringIO()
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
          
    def __enter__(self):
        sys.stdout = self.buffer
        sys.stderr = self.buffer
        return self.buffer
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

HELP = HelpCategory("EXECUTION")

HELP.add_help(["run", "r"], "run command on server",
                "runs a command on server. Shell will be from user running bot. " +
                "Every command starts in bot root folder.", args="<cmd>")
@alemiBot.on_message(is_superuser & filterCommand(["run", "r"], list(alemiBot.prefixes)))
async def runit(client, message):
    args = re.sub(r"-delme(?: |)(?:[0-9]+|)", "", message.command["raw"])
    msg = await edit_or_reply(message, "` → ` Running")
    try:
        logger.info(f"Running command \"{args}\"")
        proc = await asyncio.create_subprocess_shell(
            args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT)

        stdout, stderr = await proc.communicate()
        output = cleartermcolor(stdout.decode())
        if len(args) + len(output) > 4080:
            await msg.edit(f"```$ {args}\n → Output too long, sending as file```")
            out = io.BytesIO((f"$ {args}\n" + output).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out)
        else:
            await msg.edit(tokenize_lines(f"$ {args}\n\n" + output, mode='html'), parse_mode='html')
    except Exception as e:
        traceback.print_exc()
        await msg.edit(f"`$ {args}`\n`[!] → ` " + str(e))

HELP.add_help(["eval", "e"], "eval a python expression",
                "eval a python expression. No imports can be made nor variables can be " +
                "assigned. Some common libs are already imported. `eval` cannot have side effects. " +
                "Returned value will be printed upon successful evaluation. `stdout` won't be captured (use `.ex`). If " +
                "a coroutine is returned, it will be awaited. Use the GLOBALS object for persistence: no assignation can " +
                "be done in `eval`, but getting fields is possible. This won't tokenize large outputs per-line, " +
                "use .ex if you need that.", args="<expr>")
@alemiBot.on_message(is_superuser & filterCommand(["eval", "e"], list(alemiBot.prefixes)))
async def evalit(client, message):
    global GLOBALS
    args = re.sub(r"-delme(?: |)(?:[0-9]+|)", "", message.command["raw"])
    msg = await edit_or_reply(message, "` → ` Evaluating")
    try:
        logger.info(f"Evaluating \"{args}\"")
        result = eval(args)
        if inspect.iscoroutine(result):
            result = await result
        if len(args) + len(str(result)) > 4080:
            await msg.edit(f"```>>> {args}\n → Output too long, sending as file```")
            out = io.BytesIO((f">>> {args}\n" + str(result)).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out, parse_mode="markdown")
        else:
            await msg.edit(f"`>>>` `{args}`\n` → ` `" + str(result) + "`", parse_mode="markdown")
    except Exception as e:
        traceback.print_exc()
        await msg.edit(f"`>>>` `{args}`\n`[!] → ` " + str(e), parse_mode='markdown')

async def aexec(code, client, message): # client and message are passed so they are in scope
    global GLOBALS
    exec(
        f'async def __aex(): ' +
        ''.join(f'\n {l}' for l in code.split('\n')),
        
        locals()
    )
    return await locals()['__aex']()

HELP.add_help(["exec", "ex"], "execute python code",
                "execute python code. This, unlike `eval`, has no bounds and " +
                "**can have side effects**. Use with more caution than `eval`. " +
                "`exec` always returns `None`, but anything printed to `stdout` " +
                "will be shown. You can set anything in the GLOBALS object for " +
                "persistence. The `exec` call is wrapped to make it work with async " +
                "code.", args="<code>")
@alemiBot.on_message(is_superuser & filterCommand(["exec", "ex"], list(alemiBot.prefixes)))
async def execit(client, message):
    args = re.sub(r"-delme(?: |)(?:[0-9]+|)", "", message.command["raw"])
    fancy_args = args.replace("\n", "\n... ")
    msg = message if is_me(message) else await message.reply("`[PLACEHOLDER]`")
    await msg.edit("```" + fancy_args + "```\n` → ` Executing")
    try:
        logger.info(f"Executing \"{args}\"")
        with stdoutWrapper() as fake_stdout:
            await aexec(args, client, message)
        result = fake_stdout.getvalue()
        if len(args) + len(result) > 4080:
            await msg.edit(f"```>>> {fancy_args}\n → Output too long, sending as file```")
            out = io.BytesIO((f">>> {fancy_args}\n" + result).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out, parse_mode='markdown')
        else:
            await msg.edit(tokenize_lines(f">>> {fancy_args}\n\n" + result), parse_mode='markdown')
    except Exception as e:
        traceback.print_exc()
        await msg.edit(f"`>>> {args}`\n`[!] → ` " + str(e), parse_mode='markdown')
