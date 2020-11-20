import asyncio
import subprocess
import time
import json
import io
import os
import traceback

from pymongo import MongoClient
from datetime import datetime

from termcolor import colored

from pyrogram import filters
from pyrogram.types import Object

from bot import alemiBot

from util import batchify
from util.parse import cleartermcolor
from util.text import split_for_window
from util.permission import is_allowed
from util.message import tokenize_json, edit_or_reply, get_text, is_me
from util.user import get_username, get_channel, get_username_dict # lmaoo bad
from util.serialization import convert_to_dict
from plugins.help import HelpCategory

HELP = HelpCategory("LOG")

last_group = "N/A"

M_CLIENT = MongoClient('localhost', 27017,
    username=alemiBot.config.get("database", "username", fallback=""),
    password=alemiBot.config.get("database", "password", fallback=""))
DB = M_CLIENT.alemibot
EVENTS = DB.events

LOG_MEDIA = alemiBot.config.get("database", "log_media", fallback=False)

LOGGED_COUNT = 0

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
async def msglogger(client, message):
    global LOGGED_COUNT
    print_formatted(message.chat, message.from_user, message)
    data = convert_to_dict(message)
    EVENTS.insert_one(data)
    LOGGED_COUNT += 1
    if message.media and LOG_MEDIA:
        try: 
            await client.download_media(message, file_name="data/scraped_media/")
        except ValueError:
            pass # ignore, some messages are marked as media but have nothing to download wtf

# Log Message deletions
@alemiBot.on_deleted_messages(group=8)
async def dellogger(_, message):
    global LOGGED_COUNT
    data = convert_to_dict(message)
    for d in data:
        d["_"] = "Delete"
        d["date"] = datetime.now()
        print(colored("[DELETED]", 'red', attrs=['bold']) + " " + str(d["message_id"]))
        EVENTS.insert_one(d)
        LOGGED_COUNT += 1

def order_suffix(num, measure='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{n:3.1f} {u}{m}".format(n=num, u=unit, m=measure)
        num /= 1024.0
    return "{n:.1f} Yi{m}".format(n=num, m=measure)

HELP.add_help(["stats", "stat"], "get stats",
                "Get uptime, disk usage for media and for db, number of tracked events.", public=True)
@alemiBot.on_message(is_allowed & filters.command(["stats", "stat"], list(alemiBot.prefixes)))
async def stats_cmd(client, message):
    global LOGGED_COUNT
    count = EVENTS.count_documents({})
    size = DB.command("dbstats")['totalSize']
    memesize = float(subprocess.run( # this is bad and ugly
        ["du", "-b", "data/memes"],
                        capture_output=True).stdout.decode('utf-8').split("\t")[0])
    memenumber = len(os.listdir("data/memes"))
    mediasize = float(subprocess.run( # this is ugly too
        ["du", "-b", "data/scraped_media"],
                        capture_output=True).stdout.decode('utf-8').split("\t")[0])

    medianumber = len(os.listdir("data/scraped_media"))
    uptime = str(datetime.now() - client.start_time)
    await edit_or_reply(message, f"`→ online for {uptime} `" +
                    f"\n` → ` **{LOGGED_COUNT}** events logged (**{count}** total)" +
                    f"\n` → ` DB size **{order_suffix(size)}**" +
                    f"\n` → ` **{memenumber}** memes collected" +
                    f"\n` → ` meme folder size **{order_suffix(memesize)}**" +
                    f"\n` → ` **{medianumber}** media scraped" +
                    f"\n` → ` scraped media size **{order_suffix(mediasize)}**")

HELP.add_help(["query", "q", "log"], "interact with db",
                "make queries to the underlying database (MongoDB) to request documents. " +
                "Filters, limits and fields can be configured with arguments.", args="[-l] [-f] <query>")
@alemiBot.on_message(filters.me & filters.command(["query", "q", "log"], prefixes=".") & filters.regex(pattern=
    r"^.(?:log|query|q)(?: |)(?P<limit>-l [0-9]+|)(?: |)(?P<filter>-f [^ ]+|)(?: |)(?P<query>[^ ]+|)"
))
async def query_cmd(client, message):
    args = message.matches[0]
    try:
        if args["query"] != "":
            buf = []
            q = json.loads(args["query"])
            cursor = None
            lim = 10
            if args["limit"] != "":
                lim = int(args["limit"].replace("-l ", ""))
            if args["filter"] != "":
                filt = json.loads(args["filter"].replace("-f ", ""))
                cursor = EVENTS.find(q, filt).sort("_id", -1).limit(lim)
            else:
                cursor = EVENTS.find(q).sort("_id", -1).limit(lim)
            for doc in cursor:
                buf.append(doc)
            raw = json.dumps(buf, indent=2, default=str)
            if len(message.text.markdown) + len(tokenize_json(raw)) > 4090:
                f = io.BytesIO(raw.encode("utf-8"))
                f.name = "query.json"
                await client.send_document(message.chat.id, f, reply_to_message_id=message.message_id,
                                        caption=f"` → Query result `")
            else:
                await message.edit(message.text.markdown + "\n` → `" + tokenize_json(raw))
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))

HELP.add_help(["hist", "history"], "get edit history of a message",
                "request edit history of a message. You can specify an id or reply to a message.",
                public=True, args="[-t] [id]")
@alemiBot.on_message(is_allowed & filters.command(["history", "hist"], prefixes=".") & filters.regex(
    pattern=r"^.hist(?:ory|)(?: |)(?P<time>-t|)(?: |)(?P<id>[0-9]+|)"
))
async def hist_cmd(_, message):
    m_id = None
    args = message.matches[0]
    show_time = args["time"] == "-t"
    if message.reply_to_message is not None:
        m_id = message.reply_to_message.message_id
    elif args["id"] != "":
        m_id = int(args["id"])
    if m_id is None:
        return
    cursor = EVENTS.find( {"_": "Message", "message_id": m_id, "chat.id": message.chat.id},
            {"text": 1, "date": 1, "edit_date": 1} ).sort("_id", -1)
    out = ""
    for doc in cursor:
        if show_time:
            if "edit_date" not in doc or doc['edit_date'] is None:
                out += f"[{str(doc['date'])}] "    
            else:
                out += f"[{str(doc['edit_date'])}] "
        if "text" in doc:
            out += f"` → ` {doc['text']['markdown']}\n"
        else:
            out += f"` → ` N/A\n"
    await edit_or_reply(message, out)

HELP.add_help(["peek", "deld", "deleted", "removed"], "get deleted messages",
                "request last edited messages, from channel or globally (-g, reserved to owner). A number of " +
                "messages to peek can be specified. You can append `-json` at the end to get a json with all message data.",
                public=True, args="[-t] [-g] [num] [-json]")
@alemiBot.on_message(is_allowed & filters.command(["peek", "deld", "deleted", "removed"], prefixes=".") & filters.regex(
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
        if args["global"] != "-g" or not is_me(message):
            q["chat.id"] = message.chat.id
        cursor = EVENTS.find(q, {"message_id": 1, "date": 1} ).sort("_id", -1)
        res = []
        for doc in cursor:
            match = {}
            if "date" in doc:
                match["date"] = doc["date"]
            else:
                match["date"] = "N/A"
            match["id"] = doc["message_id"]
            try:
                msg = EVENTS.find({"_": "Message", "message_id": match["id"]}).sort("_id", -1).next()
            except StopIteration: # no message was found, maybe it's a ChatAction
                continue
            if "from_user" not in msg:
                match["author"] = "UNKNOWN"
            else:
                match["author"] = get_username_dict(msg["from_user"])
            if "text" in msg:
                match["message"] = msg["text"]["markdown"]
            else:
                match["message"] = ""
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

