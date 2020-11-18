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

from util import set_offline, batchify
from util.parse import cleartermcolor
from util.permission import is_allowed
from util.message import tokenize_json, tokenize_lines, edit_or_reply

def extract(obj):
    new_dict = {k: v for k, v in obj.__dict__.items() if v is not None}
    new_dict.pop("_client", None)
    return new_dict

# Repy to .asd with "a sunny day" (and calculate ping)
@alemiBot.on_message(filters.me & filters.command(["asd", "ping"], prefixes="."))
async def ping(_, message):
    msg = message.text
    before = time.time()
    await message.edit(msg + "\n` → ` a sunny day")
    after = time.time()
    latency = (after - before) * 1000
    await message.edit(msg + f"\n` → ` a sunny day `({latency:.0f}ms)`")

# TODO
# Update userbot (git pull + restart)
# @events.register(events.NewMessage(pattern=r"{p}update".format(p=PREFIX), outgoing=True))
# async def update(event):
#     msg = event.raw_text
#     try:
#         print(f" [ Updating bot ]")
#         msg += "\n` → ` Updating"
#         await event.message.edit(msg) 
#         result = subprocess.run(["git", "pull"], capture_output=True, timeout=60)
#         msg += " [OK]\n` → ` Bot will now restart"
#         await event.message.edit(msg) 
#         await event.client.disconnect()
#     except Exception as e:
#         msg += " [FAIL]\n`[!] → ` " + str(e)
#         await event.message.edit(msg) 
#     await set_offline(event.client)

# Get info about a chat
@alemiBot.on_message(is_allowed & filters.command("where", prefixes="."))
async def where_cmd(_, message):
    try:
        print(f" [ getting info of chat ]")
        out = " → Data : \n"
        data = extract(message.chat)
        if len(message.command) > 1 and message.command[1] == "-p":
            out += tokenize_json(str(data))
        else:
            out += str(message)
            # out += tokenize_json(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))

# Get info about a user
@alemiBot.on_message(is_allowed & filters.regex(pattern=
    r"^[\.\/]who(?: |)(?P<pack>-p|-r|)(?: |)(?P<name>[^ ]+|)"
))
async def who_cmd(client, message):
    try:
        peer = None
        if message.reply_to_message is not None \
        and message.reply_to_message.from_user is not None:
            peer = message.reply_to_message.from_user
        elif message.matches[0]["name"] != "":
            try:
                peer = await client.get_users(int(message.matches[0]["name"]))
            except:
                peer = await client.get_users(message.matches[0]["name"])
        else:
            return
        print(f" [ getting info of user ]")
        out = "` → ` Data : \n"
        data = extract(peer)
        if message.matches[0]["pack"] == "-p":
            out += tokenize_json(str(data))
        else:
            out += str(message)
            # out += tokenize_json(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Get info about a message
@alemiBot.on_message(is_allowed & filters.command("what", prefixes="."))
async def what_cmd(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = await client.get_messages(message.chat.id, message.message_id)
    print(f" [ getting info of msg ]")
    try:
        out = " → Data : \n"
        data = extract(msg)
        if "reply_to_message" in data:
            data["reply_to_message"] = extract(data["reply_to_message"])
            data["reply_to_message"].pop("chat", None) # it's in the same chat anyway, useless data
        if len(message.command) > 1 and message.command[1] == "-p":
            out += tokenize_json(str(data))
        else:
            out += str(message)
            # out += tokenize_json(json.dumps(data, indent=2, default=str, ensure_ascii=False))
        await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))

# Run command
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

# Eval python line
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

# class SystemModules:
#     def __init__(self, client, limit=False):
#         self.helptext = "`━━┫ SYSTEM `\n"
# 
#         if not limit:
#             client.add_event_handler(runit)
#             self.helptext += "`→ .run <cmd> ` execute command on server\n"
# 
#             client.add_event_handler(evalit)
#             self.helptext += "`→ .eval <cmd> ` execute python expr\n"
# 
#         client.add_event_handler(ping)
#         self.helptext += "`→ .asd ` a sunny day (+ get latency)\n"
# 
#         client.add_event_handler(who_cmd)
#         self.helptext += "`→ .who [-p|-r] [@user] ` get info of user *\n"
# 
#         client.add_event_handler(what_cmd)
#         self.helptext += "`→ .what [-p|-r] ` get info of message *\n"
# 
#         client.add_event_handler(where_cmd)
#         self.helptext += "`→ .where [-p|-r] ` get info of chat *\n"
# 
#         client.add_event_handler(update)
#         self.helptext += "`→ .update ` (git) pull changes and reboot bot\n"
# 
#         print(" [ Registered System Modules ]")
