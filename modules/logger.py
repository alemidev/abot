import asyncio
import subprocess
import datetime
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
from util.permission import is_allowed
from util.message import get_channel

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
    entry = event.message.to_dict()
    entry["WHO"] = event.sender_id
    entry["WHAT"] = "Edit"
    entry["WHERE"] = (await event.client.get_entity(event.chat_id)).id
    EVENTS.insert_one(entry)
    msg = await parse_event(event, edit=True)
    msg.print_formatted()

# This is super lazy but will do for now ig

# Print in terminal received chats
@events.register(events.NewMessage)
async def msglogger(event):
    entry = event.message.to_dict()
    entry["WHO"] = event.sender_id
    entry["WHAT"] = "New"
    entry["WHERE"] = (await event.client.get_entity(event.chat_id)).id
    EVENTS.insert_one(entry)
    msg = await parse_event(event)
    msg.print_formatted()

# Log Message deletions
@events.register(events.MessageDeleted)
async def dellogger(event):
    entry = event.to_dict()
    entry["original_update"] = entry["original_update"].to_dict()
    entry["WHO"] = "UNKNOWN" # Delete event doesn't tell you who deleted, but msgs are unique
    entry["WHAT"] = "Delete"
    if ("channel_id" in entry["original_update"] and 
            entry["original_update"]["channel_id"] is not None):
        entry["WHERE"] = entry["original_update"]["channel_id"]
    else:
        orig_msg = EVENTS.find_one({"id": entry["deleted_id"]})
        if orig_msg is not None:
            entry["WHERE"] = orig_msg["WHERE"]
        else:
            entry["WHERE"] = "UNKNOWN"
    entry["WHEN"] = datetime.datetime.now()
    EVENTS.insert_one(entry)

# Log Chat Actions
@events.register(events.ChatAction)
async def actionlogger(event):
    entry = event.to_dict()
    entry.pop("original_update", None)
    if entry["action_message"] is not None:
        entry["action_message"] = entry["action_message"].to_dict()
    if event.users is not None:
        entry["WHO"] = event.user_id
    else:
        entry["WHO"] = "UNKNOWN"
    entry["WHAT"] = "Action"
    entry["WHERE"] = (await event.client.get_entity(event.chat_id)).id
    EVENTS.insert_one(entry)

def order_suffix(num, measure='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{n:3.1f} {u}{m}".format(n=num, u=unit, m=measure)
        num /= 1024.0
    return "{n:.1f} Yi{m}".format(n=num, m=measure)

# Get data off database
@events.register(events.NewMessage(
    pattern=r"{p}(?:log|query|q)(?: |)(?P<count>-c|)(?: |)(?P<limit>-l [0-9]+|)(?: |)(?P<filter>-f [^ ]+|)(?: |)(?P<query>[^ ]+|)".format(p=PREFIX),
    outgoing=True))
async def query_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    args = event.pattern_match.groupdict()
    try:
        if args["count"] == "-c":
            count = EVENTS.count_documents({})
            size = DB.command("dbstats")['totalSize']
            await event.message.edit(event.raw_text +
                            f"\n` → ` **{count}** events logged" +
                            f"\n` → ` size **{order_suffix(size)}**")
        elif args["query"] != "":
            buf = []
            q = json.loads(args["query"])
            cursor = None
            lim = None
            if args["limit"] != "":
                lim = int(args["limit"].replace("-l ", ""))
            if args["filter"] != "":
                filt = json.loads(args["filter"].replace("-f ", ""))
                cursor = EVENTS.find(q, filt).sort("_id", -1)
            else:
                cursor = EVENTS.find(q).sort("_id", -1)
            for doc in cursor:
                buf.append(doc)
                if lim is not None and len(buf) >= lim:
                    break
            raw = json.dumps(buf, indent=2, default=str)
            if len(event.raw_text) + len(raw) > 4080:
                f = io.BytesIO(raw.encode("utf-8"))
                f.name = "query.json"
                await event.message.reply("``` → Query result```", file=f)
            else:
                await event.message.edit(event.raw_text + "\n``` → " + raw + "```")
    except Exception as e:
        traceback.print_exc()
        await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Get edit history of a message
@events.register(events.NewMessage(pattern=r"{p}hist(?:ory|)(?: |)(?P<time>-t|)(?: |)(?P<id>[0-9]+|)".format(p=PREFIX)))
async def hist_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    m_id = None
    chat = await event.get_chat()
    show_time = event.pattern_match.group("time") == "-t"
    if event.is_reply:
        msg = await event.get_reply_message()
        m_id = msg.id
    elif event.pattern_match.group("id") != "":
        m_id = int(event.pattern_match.group("id"))
    if m_id is None:
        return
    cursor = EVENTS.find( {"id": m_id, "WHERE": chat.id},
            {"message": 1, "date": 1, "edit_date": 1} ).sort("_id", -1)
    out = ""
    for doc in cursor:
        if show_time:
            if "edit_date" not in doc or doc['edit_date'] is None:
                out += f"[{str(doc['date'])}] "    
            else:
                out += f"[{str(doc['edit_date'])}] "    
        out += f"` → ` {doc['message']}\n"
    if event.out:
        await event.message.edit(event.raw_text + "\n" + out)
    else:
        await event.message.reply(out)
    await set_offline(event.client)

# Get last N deleted messages
@events.register(events.NewMessage(
        pattern=r"{p}(?:peek|deld|deleted|removed)(?: |)(?P<time>-t|)(?: |)(?P<number>[0-9]+|)".format(p=PREFIX)))
async def deleted_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    limit = 1
    show_time = event.pattern_match.group("time") == "-t"
    try:
        chat = await event.get_chat()
        if event.pattern_match.group("number") != "":
            limit = int(event.pattern_match.group("number"))
        cursor = EVENTS.find( {"WHAT": "Delete", "WHERE": chat.id },
                {"deleted_id": 1, "WHEN": 1} ).sort("_id", -1).limit(limit)
        out = ""
        for doc in cursor:
            if show_time and "WHEN" in doc:
                out += f"[{str(doc['WHEN'])}] "
            m_id = doc["deleted_id"]
            out += f"**[**`{m_id}`**]** "
            msg = EVENTS.find_one({"id": m_id})
            peer = msg["WHO"]
            if peer is None:
                out += f"`UNKN →` {msg['message']}"
                continue
            author = await event.client.get_entity(peer)
            if author is None:
                out += f"`UNKN →` {msg['message']}"
                continue
            out += f"`{get_username(author)} →` {msg['message']}\n\n"
        if out == "":
            out = "` → ` Nothing to display"
        if event.out:
            await event.message.edit(event.raw_text + "\n" + out)
        else:
            await event.message.reply(out)
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

class LoggerModules:
    def __init__(self, client, limit=False):
        self.helptext = "`━━┫ LOG `\n"

        client.add_event_handler(editlogger)
        client.add_event_handler(msglogger)
        client.add_event_handler(dellogger)
        client.add_event_handler(actionlogger)

        client.add_event_handler(query_cmd)
        self.helptext += "`→ .query [-c] [-l] [-f] [query] ` interact with db\n"

        client.add_event_handler(hist_cmd)
        self.helptext += "`→ .history [-t] [id] ` get edits to a message *\n"

        client.add_event_handler(deleted_cmd)
        self.helptext += "`→ .peek [n] [-t] ` get last (n) deleted msgs *\n"

        print(" [ Registered Logger Modules ]")
