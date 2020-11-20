import subprocess
import io
import re
import traceback
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

from util.parse import cleartermcolor
from util.message import tokenize_json, tokenize_lines
from util.serialization import convert_to_dict
from plugins.help import HelpCategory

class GlobalThings():
    def __str__(self):
        return str(convert_to_dict(self))

GLOBALS = GlobalThings()

class stdoutWrapper(): 
    def __init__(self): 
        self.stdout = io.StringIO()
        self.old_stdout = sys.stdout
          
    def __enter__(self): 
        sys.stdout = self.stdout
        return self.stdout
      
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        sys.stdout = self.old_stdout

HELP = HelpCategory("EXECUTION")

HELP.add_help(["run", "r"], "run command on server",
                "runs a command on server. Shell will be from user running bot. " +
                "Every command starts in bot root folder.", args="<cmd>")
@alemiBot.on_message(filters.me & filters.command(["run", "r"], list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.(?:run|r) (?P<cmd>.*)", flags=re.DOTALL
))
async def runit(client, message):
    args = message.matches[0]["cmd"]
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
                "assigned. Some common libs are already imported. `eval` cannot have side effects. " +
                "Anything returned by `eval` will be printed upon successful evaluation. If " +
                "a coroutine is returned, it will be awaited (needed for executing async funcs defined " +
                "with .exec). `stdout` will be captured and shown before the returned value. Use the " +
                "GLOBALS object for persistence. No assignation can be done in `eval`, but getting " +
                "fields is possible.", args="<expr>")
@alemiBot.on_message(filters.me & filters.command(["eval", "e"], list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.(?:eval|e) (?P<expr>.*)", flags=re.DOTALL
))
async def evalit(client, message):
    global GLOBALS
    args = message.matches[0]["expr"]
    try:
        print(f" [ evaluating \"{args}\" ]")
        with stdoutWrapper() as fake_stdout:
            result = eval(args)
            if inspect.iscoroutine(result):
                result = await result
        result = fake_stdout.getvalue() + " → " + str(result)
        if len(args) + len(result) > 4080:
            await message.edit(f"```>>> {args}\n → Output too long, sending as file```")
            out = io.BytesIO((f">>> {args}\n" + result).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out)
        else:
            await message.edit(tokenize_lines(f">>> {args}\n" + result))
    except Exception as e:
        traceback.print_exc()
        await message.edit(f"`>>> {args}`\n`[!] → ` " + str(e))

HELP.add_help(["exec", "ex"], "execute python code",
                "execute python code. This, unlike `eval`, has no bounds and " +
                "**can have side effects**. Use with more caution than `eval`. " +
                "`exec` always returns `None`, but anything printed to `stdout` " +
                "will be shown. You can set anything in the GLOBALS object for " +
                "persistence.", args="<code>")
@alemiBot.on_message(filters.me & filters.command(["exec", "ex"], list(alemiBot.prefixes)) & filters.regex(
    pattern=r"^.(?:exec|ex) (?P<code>.*)", flags=re.DOTALL
))
async def execit(client, message):
    global GLOBALS
    args = message.matches[0]["code"]
    fancy_args = args.replace("\n", "\n... ")
    try:
        with stdoutWrapper() as fake_stdout:
            exec(args)
        result = fake_stdout.getvalue()
        if len(args) + len(result) > 4080:
            await message.edit(f"```>>> {fancy_args}\n → Output too long, sending as file```")
            out = io.BytesIO((f">>> {fancy_args}\n" + result).encode('utf-8'))
            out.name = "output.txt"
            await client.send_document(message.chat.id, out)
        else:
            await message.edit(tokenize_lines(f">>> {fancy_args}\n\n" + result))
    except Exception as e:
        traceback.print_exc()
        await message.edit(f"`>>> {args}`\n`[!] → ` " + str(e))
