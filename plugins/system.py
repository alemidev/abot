import asyncio
import subprocess
import time
import io
import traceback
import json

# handy libs to have for eval()
import requests
import sympy
import os
import re
import random
import math
import datetime

from termcolor import colored

from bot import alemiBot

from pyrogram import filters
from pyrogram.types import InputMediaDocument

from util import batchify
from util.parse import cleartermcolor
from util.permission import is_allowed
from util.message import tokenize_json, tokenize_lines, edit_or_reply, is_me
from util.serialization import convert_to_dict
from plugins.help import HelpCategory

HELP = HelpCategory("SYSTEM")

HELP.add_help(["asd", "ping"], "a sunny day!",
                "The ping command.")
@alemiBot.on_message(filters.me & filters.command(["asd", "ping"], prefixes="."))
async def ping(_, message):
    msg = message.text.markdown
    before = time.time()
    await message.edit(msg + "\n` → ` a sunny day")
    after = time.time()
    latency = (after - before) * 1000
    await message.edit(msg + f"\n` → ` a sunny day `({latency:.0f}ms)`")

HELP.add_help("update", "update and restart",
                "will pull changes from git (`git pull`) and then restart " +
                "itself with an `execv` call.")
@alemiBot.on_message(filters.me & filters.command("update", prefixes="."))
async def update(_, message):
    msg = message.text.markdown
    try:
        print(f" [ Updating bot ]")
        msg += "\n` → ` Updating"
        await message.edit(msg) 
        result = subprocess.run(["git", "pull"], capture_output=True, timeout=60)
        msg += " [OK]\n` → ` Bot will now restart"
        await message.edit(msg) 
        await alemiBot.restart()
    except Exception as e:
        msg += " [FAIL]\n`[!] → ` " + str(e)
        await message.edit(msg) 

HELP.add_help("where", "get info about chat",
                "Get the complete information about current chat and attach as json",
                public=True)
@alemiBot.on_message(is_allowed & filters.command("where", prefixes="."))
async def where_cmd(client, message):
    try:
        print(f" [ getting info of chat ]")
        if is_me(message):
            await message.edit(message.text.markdown + f"\n` → ` Getting data of chat `{message.chat.id}`")
        out = io.BytesIO((str(message.chat)).encode('utf-8'))
        out.name = f"chat-{message.chat.id}.json"
        await client.send_document(message.chat.id, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))

HELP.add_help("who", "get info about user",
                "Get the complete information about an user (replied to or "+
                "id given) and attach as json", public=True, args="[target]")
@alemiBot.on_message(is_allowed & filters.command("who", prefixes=".") &
    filters.regex(pattern=r"^.who(?: |)(?P<name>[^ ]+|)"
))
async def who_cmd(client, message):
    try:
        peer = None
        if message.reply_to_message is not None \
        and message.reply_to_message.from_user is not None:
            peer = message.reply_to_message.from_user
        elif message.matches[0]["name"] != "":
            name = message.matches[0]["name"]
            try:
                peer = await client.get_users(int(name))
            except:
                peer = await client.get_users(name)
        else:
            return
        print(f" [ getting info of user ]")
        if is_me(message):
            await message.edit(message.text.markdown + f"\n` → ` Getting data of user `{peer.id}`")
        out = io.BytesIO((str(peer)).encode('utf-8'))
        out.name = f"user-{peer.id}.json"
        await client.send_document(message.chat.id, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help("what", "get info about message",
                "Get the complete information about a message (replied to or "+
                "the sent message) and attach as json", public=True)
@alemiBot.on_message(is_allowed & filters.command("what", prefixes="."))
async def what_cmd(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = await client.get_messages(message.chat.id, message.message_id)
    print(f" [ getting info of msg ]")
    try:
        if is_me(message):
            await message.edit(message.text.markdown + f"\n` → ` Getting data of msg `{msg.message_id}`")
        out = io.BytesIO((str(msg)).encode('utf-8'))
        out.name = f"msg-{msg.message_id}.json"
        await client.send_document(message.chat.id, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))

HELP.add_help(["run", "r"], "run command on server",
                "runs a command on server. Shell will be from user running bot. " +
                "Every command starts in bot root folder.", args="<cmd>")
@alemiBot.on_message(filters.me & filters.command(["run", "r"], prefixes="."))
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
@alemiBot.on_message(filters.me & filters.command(["eval", "e"], prefixes="."))
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
