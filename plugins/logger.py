import asyncio
import subprocess
import time
import json
import logging
import io
import os
import traceback
import queue

from pymongo import MongoClient
from datetime import datetime

from termcolor import colored

from pyrogram import filters
from pyrogram.types import Object
from pyrogram.errors.exceptions.flood_420 import FloodWait

from bot import alemiBot

from util import batchify
from util.parse import cleartermcolor
from util.text import split_for_window
from util.permission import is_allowed
from util.message import tokenize_json, edit_or_reply, get_text, get_text_dict, is_me
from util.user import get_username, get_username_dict # lmaoo bad
from util.chat import get_channel, get_channel_dict
from util.serialization import convert_to_dict
from plugins.help import HelpCategory

import logging
lgr = logging.getLogger(__name__)

HELP = HelpCategory("LOG")

LAST_GROUP = "N/A"

M_CLIENT = MongoClient('localhost', 27017,
    username=alemiBot.config.get("database", "username", fallback=""),
    password=alemiBot.config.get("database", "password", fallback=""))
DB = M_CLIENT.alemibot
EVENTS = DB.events

LOG_MEDIA = alemiBot.config.get("database", "log_media", fallback=False)

LOGGED_COUNT = 0

def print_formatted(chat, user, message):
    global LAST_GROUP
    if chat.id != LAST_GROUP:
        print(colored("━━━━━━━━━━┫ " + get_channel(chat), 'cyan', attrs=['bold']))
    LAST_GROUP = chat.id
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
@alemiBot.on_message(group=10)
async def msglogger(client, message):
    global LOGGED_COUNT
    # print_formatted(message.chat, message.from_user, message)
    data = convert_to_dict(message)
    if message.media and LOG_MEDIA and message.edit_date is None: # don't redownload media at edits!
        try: 
            fname = await client.download_media(message, file_name="data/scraped_media/")
            if fname is not None:
                data["attached_file"] = fname.split("data/scraped_media/")[1]
        except ValueError:
            pass # ignore, some messages are marked as media but have nothing to download wtf
    EVENTS.insert_one(data)
    LOGGED_COUNT += 1

# Log Message deletions
@alemiBot.on_deleted_messages(group=10)
async def dellogger(client, message):
    global LOGGED_COUNT
    data = convert_to_dict(message)
    for d in data:
        d["_"] = "Delete"
        d["date"] = datetime.now()
        # print(colored("[DELETED]", 'red', attrs=['bold']) + " " + str(d["message_id"]))
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
    lgr.info("Getting stats")
    global LOGGED_COUNT
    count = EVENTS.count({})
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
                    f"\n` → ` **{LOGGED_COUNT}** events monitored (**{count}** total)" +
                    f"\n` → ` DB size **{order_suffix(size)}**" +
                    f"\n` → ` **{memenumber}** memes collected" +
                    f"\n` → ` meme folder size **{order_suffix(memesize)}**" +
                    f"\n` → ` **{medianumber}** documents archived" + # lmao don't call it scraped_media maybe
                    f"\n` → ` archive size **{order_suffix(mediasize)}**")
    await client.set_offline()

HELP.add_help(["query", "q", "log"], "interact with db",
                "make queries to the underlying database (MongoDB) to request documents. " +
                "Filters, limits and fields can be configured with arguments.", args="[-l <n>] [-f <{filter}>] <{query}>")
@alemiBot.on_message(filters.me & filters.command(["query", "q", "log"], prefixes=".") & filters.regex(pattern=
    r"^.(?:log|query|q)(?: |)(?P<limit>-l [0-9]+|)(?: |)(?P<filter>-f [^ ]+|)(?: |)(?P<query>[^ ]+|)"
))
async def query_cmd(client, message):
    args = message.matches[0]
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        if args["query"] != "":
            buf = []
            q = json.loads(args["query"])
            cursor = None
            lim = 10
            if args["limit"] != "":
                lim = int(args["limit"].replace("-l ", ""))
            lgr.info("Querying db : {args['query']}")

            if args["filter"] != "":
                filt = json.loads(args["filter"].replace("-f ", ""))
                cursor = EVENTS.find(q, filt).sort("_id", -1).limit(lim)
            else:
                cursor = EVENTS.find(q).sort("_id", -1).limit(lim)

            for doc in cursor:
                buf.append(doc)

            raw = json.dumps(buf, indent=2, default=str, ensure_ascii=False)
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
    await client.send_chat_action(message.chat.id, "cancel")

HELP.add_help(["hist", "history"], "get edit history of a message",
                "request edit history of a message. You can specify an id or reply to a message.",
                public=True, args="[-t] [-g <g>] [<id>]")
@alemiBot.on_message(is_allowed & filters.command(["history", "hist"], prefixes=".") & filters.regex(
    pattern=r"^.hist(?:ory|)(?: |)(?P<time>-t|)(?: |)(?P<group>-g [0-9]+|)(?: |)(?P<id>[0-9]+|)"
))
async def hist_cmd(client, message):
    m_id = None
    c_id = message.chat.id
    args = message.matches[0]
    show_time = args["time"] == "-t"
    if message.reply_to_message is not None:
        m_id = message.reply_to_message.message_id
    elif args["id"] != "":
        m_id = int(args["id"])
    if m_id is None:
        return
    if args["group"].startswith("-g "):
        c_id = int(args["group"].replace("-g ", ""))
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        cursor = EVENTS.find( {"_": "Message", "message_id": m_id, "chat.id": c_id},
                {"text": 1, "date": 1, "edit_date": 1} ).sort("_id", -1)
        lgr.info("Querying db for message history")
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
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + "\n`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()


async def lookup_deleted_messages(client, message, target_group, limit, show_time=False):
    response = await edit_or_reply(message, f"` → Peeking {limit} message{'s' if limit > 1 else ''} " +
                                            ('in ' + target_group.title if target_group is not None else '') + "`")
    chat_id = target_group.id if target_group is not None else None
    out = response.text.html + "\n\n"
    count = 0
    LINE = "`[{m_id}]` **{user}** `→ {where}` {text} {media}\n"
    try:
        lgr.debug("Querying db for deletions")
        await client.send_chat_action(message.chat.id, "upload_document")
        cursor = EVENTS.find({ "_": "Delete" }).sort("_id", -1)
        for deletion in cursor: # TODO make this part not a fucking mess!
            if chat_id is not None and "chat" in deletion \
            and deletion["chat"]["id"] != chat_id:
                continue # don't make a 2nd query, should speed up a ton
            candidates = EVENTS.find({"_": "Message", "message_id": deletion["message_id"]}).sort("_id", -1).limit(50)
            lgr.debug("Querying db for possible deleted msg")
            for doc in candidates: # dank 'for': i only need one
                if chat_id is not None and doc["chat"]["id"] != chat_id:
                    continue
                if "service" in doc and doc["service"]:
                    break # we don't care about service messages!
                if "from_user" in doc and doc["from_user"]["is_bot"]:
                    break # we don't care about bot messages!
                if limit == 1 and "attached_file" in doc:
                    await client.send_document(message.chat.id, "data/scraped_media/"+doc["attached_file"], reply_to_message_id=message.message_id,
                                        caption="**" + (get_username_dict(doc['from_user']) if "from_user" in doc else "UNKNOWN") + "** `→" +
                                                (' ' + get_channel_dict(doc['chat']) + ' →' if chat_id is None else '') +
                                                f"` {get_text_dict(doc)['raw']}")
                else:
                    out += LINE.format(m_id=doc["message_id"], user=get_username_dict(doc["from_user"]),
                                    where='' if chat_id is not None else (' ' + get_channel_dict(doc["chat"]) + ' →'),
                                    text=get_text_dict(doc)['raw'], media=('' if "attached_file" not in doc else ('(--' + doc["attached_file"] + '--)')))
                count += 1
                break
            if count >= limit:
                break
        if count > 0:
            if len(out) > 4096:
                for m in batchify(out, 4090):
                    await response.reply(m)
            else:
                await response.edit(out)
        else:
            await response.edit(out + "**N/A**")
    except Exception as e:
        traceback.print_exc()
        await response.edit(out + "\n\n`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline() 

HELP.add_help(["peek", "deld", "deleted", "removed"], "get deleted messages",
                "request last deleted messages in this channel. Use `-t` to add timestamps. A number of " +
                "messages to peek can be specified. just message data. Messages " +
                "from bots or system messages will be skipped in peek (use manual " +
                "queries if you need to log those). Owner can peek globally (`-g`) or in a specific group (`-g <id>`)",
                public=True, args="[-t] [<num>] [-g [id]]")
@alemiBot.on_message(is_allowed & filters.command(["peek", "deld", "deleted", "removed"], prefixes=".") & filters.regex(
    pattern=r"^.(?:peek|deld|deleted|removed)(?: |)(?P<time>-t|)(?: |)(?P<number>[0-9]+|)(?: |)(?P<global>-g [0-9\-]+|-g|)"
))
async def deleted_cmd(client, message): # This is a mess omg
    args = message.matches[0]
    show_time = args["time"] == "-t"
    target_group = message.chat
    if is_me(message) and args["global"].startswith("-g"):
        if args["global"] == "-g":
            target_group = None
        else:
            target_group = await client.get_chat(int(args["global"].replace("-g ", "")))
    limit = 1
    if args["number"] != "":
        limit = int(args["number"])
    lgr.info(f"Peeking {limit} messages")
    asyncio.get_event_loop().create_task( # launch the task async because it may take some time
        lookup_deleted_messages(
            client, message,
            target_group, limit, show_time
            )
        )

