import asyncio
import subprocess
import time
import json
import io
import traceback

from pymongo import MongoClient

from termcolor import colored

from telethon import events

from util import can_react, set_offline, batchify
from util.parse import cleartermcolor
from util.globals import PREFIX
from util.user import get_username
from util.text import split_for_window

last_group = "N/A"

M_CLIENT = MongoClient('localhost', 27017)
DB = M_CLIENT.telegram
EVENTS = DB.events

class MessageEntry:
    def __init__(self, channel, author, message, media):
        self.channel = channel
        self.author = author
        self.message = message
        self.media = media

    def print_formatted(self):
        global last_group
        if self.channel != last_group:
            print(colored("━━━━━━━━━━┫ " + self.channel, 'cyan', attrs=['bold']))
        last_group = self.channel
        pre = len(self.author) + 3
        text = self.message.replace("\n", "\n" + " "*pre)
        if self.media:
            text = "[+MEDIA] " + text
        text = split_for_window(text, offset=pre)
        print(f"{colored(self.author, 'cyan')} {colored('→', 'grey')} {text}")
        
async def parse_event(event, edit=False):
    chat = await event.get_chat()
    author = "UNKNOWN"
    chan = "UNKNOWN"
    msg = event.raw_text
    if edit:
        msg = "[EDIT] " + msg

    if hasattr(chat, 'title'):      # check if this is a group but I found
        chan = chat.title           # no better way (for now)
    else:
        chan = get_username(chat)   # in DMs, get_chat returns an User

    peer = await event.get_input_sender()
    if peer is None:
        author = chan
    else:
        sender = await event.client.get_entity(peer)
        author = get_username(sender)
    media = event.message.media is not None
    return MessageEntry(chan, author, msg, media)

# Print in terminal received edits
@events.register(events.MessageEdited)
async def editlogger(event):
    EVENTS.insert_one(event.message.to_dict())
    msg = await parse_event(event, edit=True)
    msg.print_formatted()

# This is super lazy but will do for now ig

# Print in terminal received chats
@events.register(events.NewMessage)
async def msglogger(event):
    EVENTS.insert_one(event.message.to_dict())
    msg = await parse_event(event)
    msg.print_formatted()

# Get data off database
@events.register(events.NewMessage(
    pattern=r"{p}log(?: |)(?P<count>-c|)(?: |)(?P<filter>-f [^ ]+|)(?: |)(?P<query>[^ ]+|)".format(p=PREFIX),
    outgoing=True))
async def log_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    args = event.pattern_match.groupdict()
    try:
        if args["count"] == "-c":
            c = EVENTS.count_documents({})
            await event.message.edit(event.raw_text + f"\n` → ` **{c}**")
        elif args["query"] != "":
            buf = [ { "query" : args["query"] } ]
            filt = {}
            if args["filter"] != "":
                filt = json.loads(args["filter"].replace("-f ", ""))
            cursor = EVENTS.find(json.loads(args["query"]), filt)
            for doc in cursor:
                buf.append(doc)
            f = io.BytesIO(json.dumps(buf, indent=2, default=str).encode("utf-8"))
            f.name = "query.json"
            await event.message.reply("``` → Query result```", file=f)
    except Exception as e:
        traceback.print_exc()
        await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

class LoggerModules:
    def __init__(self, client, limit=False):
        self.helptext = "`━━┫ LOG `\n"

        client.add_event_handler(editlogger)
        client.add_event_handler(msglogger)

        client.add_event_handler(log_cmd)
        self.helptext += "`→ .log [-c] [-f] [query] ` interact with db\n"

        print(" [ Registered Logger Modules ]")
