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

from telethon import events

from util import set_offline, batchify
from util.parse import cleartermcolor
from util.globals import PREFIX
from util.permission import is_allowed
from util.message import tokenize_json, tokenize_lines

# Repy to .asd with "a sunny day" (and calculate ping)
@events.register(events.NewMessage(pattern=r"{p}asd".format(p=PREFIX), outgoing=True))
async def ping(event):
    msg = event.raw_text
    before = time.time()
    await event.message.edit(msg + "\n` → ` a sunny day")
    after = time.time()
    latency = (after - before) * 1000
    await event.message.edit(msg + f"\n` → ` a sunny day `({latency:.0f}ms)`")
    await set_offline(event.client)

# Update userbot (git pull + restart)
@events.register(events.NewMessage(pattern=r"{p}update".format(p=PREFIX), outgoing=True))
async def update(event):
    msg = event.raw_text
    try:
        print(f" [ Updating bot ]")
        msg += "\n` → ` Updating"
        await event.message.edit(msg) 
        result = subprocess.run(["git", "pull"], capture_output=True, timeout=60)
        msg += " [OK]\n` → ` Bot will now restart"
        await event.message.edit(msg) 
        await event.client.disconnect()
    except Exception as e:
        msg += " [FAIL]\n`[!] → ` " + str(e)
        await event.message.edit(msg) 
    await set_offline(event.client)

# Get info about a chat
@events.register(events.NewMessage(pattern=r"{p}where(?: |)(?P<pack>-p|-r|)".format(p=PREFIX)))
async def where_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        chat = await event.get_chat()
        print(f" [ getting info of chat ]")
        out = " → Data : \n"
        if event.pattern_match.group("pack") == "-p":
            out += tokenize_json(str(chat.to_dict()))
        elif event.pattern_match.group("pack") == "-r":
            out += tokenize_json(chat.stringify())
        else:
            out += tokenize_json(json.dumps(chat.to_dict(), indent=2, default=str))
        for m in batchify(out, 4090):
            await event.message.reply(m)
    except Exception as e:
        traceback.print_exc()
        await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Get info about a user
@events.register(events.NewMessage(pattern=r"{p}who(?: |)(?P<pack>-p|-r|)(?: |)(?P<name>[^ ]+|)".format(p=PREFIX)))
async def who_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        peer = None
        if event.is_reply:
            msg = await event.get_reply_message()
            peer = await msg.get_input_sender()
            if peer is None:
                return
            peer = await event.client.get_entity(peer)
        elif event.pattern_match.group("name") != "":
            try:
                peer = await event.client.get_entity(int(event.pattern_match.group("name")))
            except ValueError:
                peer = await event.client.get_entity(event.pattern_match.group("name"))
        else:
            return
        print(f" [ getting info of user ]")
        out = "` → ` Data : \n"
        if event.pattern_match.group("pack") == "-p":
            out += tokenize_json(str(peer.to_dict()))
        elif event.pattern_match.group("pack") == "-r":
            out += tokenize_json(peer.stringify())
        else:
            out += tokenize_json(json.dumps(peer.to_dict(), indent=2, default=str))
        for m in batchify(out, 4090):
            await event.message.reply(m)
    except Exception as e:
        traceback.print_exc()
        await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Get info about a message
@events.register(events.NewMessage(pattern=r"{p}what(?: |)(?P<pack>-p|-r|)".format(p=PREFIX)))
async def what_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    print(f" [ getting info of msg ]")
    try:
        out = " → Data : \n"
        if event.pattern_match.group("pack") == "-p":
            out += tokenize_json(str(msg.to_dict()))
        elif event.pattern_match.group("pack") == "-r":
            out += tokenize_json(msg.stringify())
        else:
            out += tokenize_json(json.dumps(msg.to_dict(), indent=2, default=str))
        for m in batchify(out, 4080):
            await event.message.reply(m)
    except Exception as e:
        traceback.print_exc()
        await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Run command
@events.register(events.NewMessage(pattern=r"{p}(?:run|r) (?P<cmd>.*)".format(p=PREFIX), outgoing=True))
async def runit(event):
    try:
        args = event.pattern_match.group("cmd")
        print(f" [ running command \"{args}\" ]")
        result = subprocess.run(args, shell=True, capture_output=True, timeout=60)
        output = cleartermcolor(result.stdout.decode())
        if len(args) + len(output) > 4080:
            out = io.BytesIO((f"$ {args}\n" + output).encode("utf-8"))
            out.name = "output.txt"
            await event.message.reply("``` → Output too long to display```", file=out)
        else:
            await event.message.edit(tokenize_lines(f"$ {args}\n\n" + output))
    except Exception as e:
        await event.message.edit(f"`$ {args}`\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Eval python line
@events.register(events.NewMessage(pattern=r"{p}(?:eval|e) (?P<cmd>.*)".format(p=PREFIX), outgoing=True))
async def evalit(event):
    try:
        args = event.pattern_match.group("cmd")
        print(f" [ evaluating \"{args}\" ]")
        result = str(eval(args))
        if len(args) + len(result) > 4080:
            out = io.BytesIO((f">>> {args}\n" + result).encode("utf-8"))
            out.name = "output.txt"
            await event.message.reply("``` → Output too long to display```", file=out)
        else:
            await event.message.edit(tokenize_lines(f">>> {args}\n\n" + result))
    except Exception as e:
        await event.message.edit(f"`>>> {args}`\n`[!] → ` " + str(e))
    await set_offline(event.client)

class SystemModules:
    def __init__(self, client, limit=False):
        self.helptext = "`━━┫ SYSTEM `\n"

        if not limit:
            client.add_event_handler(runit)
            self.helptext += "`→ .run <cmd> ` execute command on server\n"

            client.add_event_handler(evalit)
            self.helptext += "`→ .eval <cmd> ` execute python expr\n"

        client.add_event_handler(ping)
        self.helptext += "`→ .asd ` a sunny day (+ get latency)\n"

        client.add_event_handler(who_cmd)
        self.helptext += "`→ .who [-p|-r] [@user] ` get info of user *\n"

        client.add_event_handler(what_cmd)
        self.helptext += "`→ .what [-p|-r] ` get info of message *\n"

        client.add_event_handler(where_cmd)
        self.helptext += "`→ .where [-p|-r] ` get info of chat *\n"

        client.add_event_handler(update)
        self.helptext += "`→ .update ` (git) pull changes and reboot bot\n"

        print(" [ Registered System Modules ]")
