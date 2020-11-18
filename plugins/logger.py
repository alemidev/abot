import asyncio
import subprocess
import datetime
import time
import json
import io
import traceback

from pymongo import MongoClient

from termcolor import colored

from pyrogram import filters

from bot import alemiBot

from util import batchify
from util.parse import cleartermcolor
from util.text import split_for_window
from util.permission import is_allowed
from util.message import tokenize_json, edit_or_reply, get_text
from util.user import get_username, get_channel

last_group = "N/A"

M_CLIENT = MongoClient('localhost', 27017, # ye TODO
                        username=alemiBot.config.get("database", "username", fallback=""),
                        password=alemiBot.config.get("database", "password", fallback=""))
DB = M_CLIENT.alemibot
EVENTS = DB.events

def print_formatted(chat, user, message):
    global last_group
    if chat.id != last_group:
        print(colored("━━━━━━━━━━┫ " + get_channel(chat), 'cyan', attrs=['bold']))
    last_group = chat.id
    u_name = get_username(user)
    pre = len(u_name) + 3
    text = get_text(message).replace("\n", "\n" + " "*pre)
    if message.media:
        text = "[+MEDIA] " + text
    if message.edit_date is not None:
        text = "[EDIT] " + text
    text = split_for_window(text, offset=pre)
    print(f"{colored(u_name, 'cyan')} {colored('→', 'grey')} {text}")

# Print in terminal received chats
@alemiBot.on_message(group=8)
async def msglogger(_, message):
    print_formatted(message.chat, message.from_user, message)
    data = json.loads(str(message)) # LMAOOO I literally could not find a better way
    EVENTS.insert_one(data)

# Log Message deletions
@alemiBot.on_deleted_messages(group=8)
async def dellogger(_, message):
    data = json.loads(str(message))
    for d in data:
        d["_"] = "Delete"
        print(colored("[DELETED]", 'red', attrs=['bold']) + " " + str(d["message_id"]))
        EVENTS.insert_one(d)

def order_suffix(num, measure='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{n:3.1f} {u}{m}".format(n=num, u=unit, m=measure)
        num /= 1024.0
    return "{n:.1f} Yi{m}".format(n=num, m=measure)

# Get data off database
@alemiBot.on_message(filters.me & filters.command(["query", "q", "log"], prefixes=".") & filters.regex(pattern=
    r"^.(?:log|query|q)(?: |)(?P<count>-c|)(?: |)(?P<limit>-l [0-9]+|)(?: |)(?P<filter>-f [^ ]+|)(?: |)(?P<query>[^ ]+|)"
))
async def query_cmd(client, message):
    args = message.matches[0]
    try:
        if args["count"] == "-c":
            count = EVENTS.count_documents({})
            size = DB.command("dbstats")['totalSize']
            await message.edit(message.text +
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
            if len(message.text) + len(tokenize_json(raw)) > 4090:
                f = io.BytesIO(raw.encode("utf-8"))
                f.name = "query.json"
                await client.send_document(message.chat.id, f, reply_to_message_id=message.message_id,
                                        caption=f"` → Query result `")
            else:
                await message.edit(message.text + "\n` → `" + tokenize_json(raw))
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text + "\n`[!] → ` " + str(e))

# Get edit history of a message
@alemiBot.on_message(is_allowed & filters.command(["history", "hist"], prefixes=".") & filters.regex(
    pattern=r"^.hist(?:ory|)(?: |)(?P<time>-t|)(?: |)(?P<id>[0-9]+|)"
))
async def hist_cmd(_, message):
    m_id = None
    args = message.matches[0]
    show_time = args["time"] == "-t"
    if message.reply_from_message is not None:
        m_id = message.reply_from_message.message_id
    elif args["id"] != "":
        m_id = int(args["id"])
    if m_id is None:
        return
    cursor = EVENTS.find( {"message_id": m_id}, # TODO search only messages in this chat
            {"message": 1, "date": 1, "edit_date": 1} ).sort("_id", -1)
    out = ""
    for doc in cursor:
        if show_time:
            if "edit_date" not in doc or doc['edit_date'] is None:
                out += f"[{str(doc['date'])}] "    
            else:
                out += f"[{str(doc['edit_date'])}] "
        out += f"` → ` {doc['message']}\n"
    await edit_or_reply(message, out)

# Get last N deleted messages
@alemiBot.on_message(filters.me & filters.command(["peek", "deld", "deleted", "removed"], prefixes=".") & filters.regex(
    pattern=r"^.(?:peek|deld|deleted|removed)(?: |)(?P<time>-t|)(?: |)(?P<global>-g|)(?: |)(?P<number>[0-9]+|)(?: |)(?P<json>-json|)"
))
async def deleted_cmd(client, message):
    limit = 1
    args = message.matches[0]
    show_time = args["time"] == "-t"
    try:
        if args["number"] != "":
            limit = int(args["number"])
        q = { "_": "Delete" }
        if args["global"] != "-g" or message.from_user is None or not message.from_user.is_self:
            q["chat"] = { "id" : message.chat.id } # this breaks searching actually TODO
        cursor = EVENTS.find(q, {"deleted_id": 1, "date": 1} ).sort("_id", -1)
        res = []
        for doc in cursor:
            match = {}
            match["date"] = doc["date"]
            match["id"] = doc["deleted_id"]
            try:
                msg = EVENTS.find({"id": match["id"]}).sort("_id", -1).next()
            except StopIteration: # no message was found, maybe it's a ChatAction
                continue
            peer = get_username(msg["from_user"])
            if peer is None:
                match["author"] = "UNKNOWN"
            match["message"] = msg["message"]
            res.append(match)
            limit -= 1
            if limit <= 0:
                break
        if args["json"] == "-json":
            f = io.BytesIO(json.dumps(res, indent=2, default=str).encode('utf-8'))
            f.name = "peek.json"
            await client.send_document(message.chat.id, f, reply_to_message_id=message.message_id,
                                        caption=f"` → Peek result `")
        else:
            out = ""
            for doc in res:
                if show_time:
                    out += f"[{str(doc['date'])}] "
                out += f"**[**`{doc['id']}`**]** `{doc['author']} →` {doc['message']}\n\n"
            if out == "":
                out = "` → ` Nothing to display"
            await edit_or_reply(message, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# class LoggerModules:
#     def __init__(self, client, limit=False):
#         self.helptext = "`━━┫ LOG `\n"
# 
#         client.add_event_handler(editlogger)
#         client.add_event_handler(msglogger)
#         client.add_event_handler(dellogger)
#         client.add_event_handler(actionlogger)
# 
#         client.add_event_handler(query_cmd)
#         self.helptext += "`→ .query [-c] [-l] [-f] [query] ` interact with db\n"
# 
#         client.add_event_handler(hist_cmd)
#         self.helptext += "`→ .history [-t] [id] ` get edits to a message *\n"
# 
#         client.add_event_handler(deleted_cmd)
#         self.helptext += "`→ .peek [-t] [-g] [n] [-json] ` show deletions *\n"
# 
#         print(" [ Registered Logger Modules ]")
