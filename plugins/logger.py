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
from util.command import filterCommand
from util.text import split_for_window
from util.permission import is_allowed
from util.message import tokenize_json, edit_or_reply, get_text, get_text_dict, is_me, parse_sys_dict
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
DB = M_CLIENT[alemiBot.config.get("database", "dbname", fallback="alemibot")]
EVENTS = DB[alemiBot.config.get("database", "collection", fallback="events")]

LOG_MEDIA = alemiBot.config.getboolean("database", "log_media", fallback=False)

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
@alemiBot.on_message(is_allowed & filterCommand(["stats", "stat"], list(alemiBot.prefixes)))
async def stats_cmd(client, message):
    lgr.info("Getting stats")
    global LOGGED_COUNT
    original_text = message.text.markdown
    before = time.time()
    msg = await edit_or_reply(message, "` → ` Fetching stats...")
    after = time.time()
    latency = (after - before) * 1000
    count = EVENTS.count({})
    size = DB.command("collstats", alemiBot.config.get("database", "collection", fallback="events"))['totalSize']
    memesize = float(subprocess.run( # this is bad and ugly
        ["du", "-b", "data/memes"],
                        capture_output=True).stdout.decode('utf-8').split("\t")[0])
    memenumber = len(os.listdir("data/memes"))
    mediasize = float(subprocess.run( # this is ugly too
        ["du", "-b", "data/scraped_media"],
                        capture_output=True).stdout.decode('utf-8').split("\t")[0])

    medianumber = len(os.listdir("data/scraped_media"))
    uptime = str(datetime.now() - client.start_time)
    await msg.edit(original_text + f"\n`→ online for {uptime} `" +
                    f"\n` → ` latency **{latency:.0f}**ms" +
                    f"\n` → ` **{LOGGED_COUNT}** events logged (**{count}** total)" +
                    f"\n` → ` DB size **{order_suffix(size)}**" +
                    f"\n` → ` **{memenumber}** memes collected" +
                    f"\n` → ` meme folder size **{order_suffix(memesize)}**" +
                    f"\n` → ` **{medianumber}** documents archived" + # lmao don't call it scraped_media maybe
                    f"\n` → ` archive size **{order_suffix(mediasize)}**")
    await client.set_offline()

HELP.add_help(["query", "q", "log"], "interact with db",
                "make queries to the underlying database (MongoDB) to request documents. " +
                "Filters, limits and fields can be configured with arguments. If multiple userbots are logging in the same " +
                "database (but in different collections), you can specify in which collection to query with `-coll`. You can also " +
                "specify which database to use with `-db` option, but the user which the bot is using to login will need permissions to read.",
                args="[-coll <name>] [-db <name>] [-l <n>] [-f <{filter}>] <{query}>")
@alemiBot.on_message(filters.me & filterCommand(["query", "q", "log"], list(alemiBot.prefixes), options={
    "limit" : ["-l", "-limit"],
    "filter" : ["-f", "-filter"],
    "collection" : ["-coll", "-collection"],
    "database" : ["-db", "-database"]
}, flags=["-cmd"]))
async def query_cmd(client, message):
    args = message.command
    try:
        if "arg" in args:
            buf = []
            cursor = None
            lim = 10
            if "limit" in args:
                lim = int(args["limit"])
            lgr.info(f"Querying db : {args['arg']}")
            
            database = DB
            if "database" in args:
                database = M_CLIENT[args["database"]]
            collection = EVENTS
            if "collection" in args:
                collection = database[args["collection"]]

            if "-cmd" in args["flags"]:
                cursor = [ database.command(*args["cmd"]) ] # ewww but small patch
            elif "filter" in args:
                q = json.loads(args["cmd"][0])
                filt = json.loads(args["filter"])
                cursor = collection.find(q, filt).sort("date", -1).limit(lim)
            else:
                cursor = collection.find(json.loads(args["cmd"][0])).sort("date", -1).limit(lim)

            for doc in cursor:
                buf.append(doc)

            raw = json.dumps(buf, indent=2, default=str, ensure_ascii=False)
            if len(message.text.markdown) + len(tokenize_json(raw)) > 4090:
                f = io.BytesIO(raw.encode("utf-8"))
                f.name = "query.json"
                await client.send_document(message.chat.id, f, reply_to_message_id=message.message_id,
                                        caption=f"` → Query result `")
            else:
                await edit_or_reply(message, "` → `" + tokenize_json(raw))
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help(["hist", "history"], "get edit history of a message",
                "request edit history of a message. You can specify an id or reply to a message.",
                public=True, args="[-t] [-g <g>] [<id>]")
@alemiBot.on_message(is_allowed & filterCommand(["history", "hist"], list(alemiBot.prefixes), options={
    "group" : ["-g"]
}, flags=["-t"]))
async def hist_cmd(client, message):
    args = message.command
    m_id = None
    c_id = message.chat.id
    show_time = "-t" in args["flags"]
    if message.reply_to_message is not None:
        m_id = message.reply_to_message.message_id
    elif "arg" in args:
        m_id = int(args["arg"])
    if m_id is None:
        return
    if "group" in args:
        c_id = int(args["group"])
    try:
        await client.send_chat_action(message.chat.id, "upload_document")
        cursor = EVENTS.find( {"_": "Message", "message_id": m_id, "chat.id": c_id},
                {"text": 1, "date": 1, "edit_date": 1} ).sort("date", -1)
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
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline()


async def lookup_deleted_messages(client, message, COLLECTION, target_group, limit, show_time=False, include_system=False, offset=0):
    response = await edit_or_reply(message, f"` → Peeking {limit} message{'s' if limit > 1 else ''} " +
                                            ('in ' + get_channel(target_group) if target_group is not None else '') + "`")
    chat_id = target_group.id if target_group is not None else None
    out = "\n\n"
    count = 0
    LINE = "{time}`[{m_id}]` **{user}** {where} → {system}{text} {media}\n"
    try:
        lgr.debug("Querying db for deletions")
        await client.send_chat_action(message.chat.id, "upload_document")
        cursor = COLLECTION.find({ "_": "Delete" }).sort("date", -1)
        for deletion in cursor: # TODO make this part not a fucking mess!
            if chat_id is not None and "chat" in deletion \
            and deletion["chat"]["id"] != chat_id:
                continue # don't make a 2nd query, should speed up a ton
            candidates = COLLECTION.find({"_": "Message", "message_id": deletion["message_id"]}).sort("date", -1)
            lgr.debug("Querying db for possible deleted msg")
            for doc in candidates: # dank 'for': i only need one
                if chat_id is not None and ("chat" not in doc or doc["chat"]["id"] != chat_id):
                    continue
                if not include_system and "service" in doc and doc["service"]:
                    break # we don't care about service messages!
                if not include_system and "from_user" in doc and doc["from_user"]["is_bot"]:
                    break # we don't care about bot messages!
                if offset > 0: # We found a message but we don't want it because an offset was set
                    offset -=1 #   skip adding this to output
                    break
                if limit == 1 and "attached_file" in doc: # Doing this here forces me to do ugly stuff below, eww!
                    await client.send_document(message.chat.id, "data/scraped_media/"+doc["attached_file"], reply_to_message_id=message.message_id,
                                        caption="**" + (get_username_dict(doc['from_user']) if "from_user" in doc else "UNKNOWN") + "** `→" +
                                                (get_channel_dict(doc['chat']) + ' → ' if chat_id is None else '') +
                                                f"` {get_text_dict(doc)['raw']}")
                else:
                    out += LINE.format(time=(str(doc["date"]) + " ") if show_time else "",
                                    m_id=doc["message_id"], user=(get_username_dict(doc["from_user"]) if "from_user" in doc else "UNKNOWN"),
                                    where='' if chat_id is not None else ("| --" + get_channel_dict(doc["chat"]) + '-- '),
                                    system=("--" + parse_sys_dict(doc) + "-- " if "service" in doc and doc["service"] else ""),
                                    text=get_text_dict(doc)['raw'], media=('' if "attached_file" not in doc else ('(`' + doc["attached_file"] + '`)')))
                count += 1
                break
            if count >= limit:
                break
        if count > 0:
            if len(out) > 4096:
                for m in batchify(out, 4090):
                    await response.reply(m)
            elif out.strip() != "": # This is bad!
                await response.edit(response.text + out)
        else:
            await response.edit(response.text + "**N/A**")
    except Exception as e:
        traceback.print_exc()
        await response.edit(response.text + "\n`[!] → ` " + str(e))
    await client.send_chat_action(message.chat.id, "cancel")
    await client.set_offline() 

HELP.add_help(["peek", "deld", "deleted", "removed"], "get deleted messages",
                "request last deleted messages in this channel. Use `-t` to add timestamps. A number of messages to peek can be specified. " +
                "If only one message is being peeked, any media attached will be included, otherwise the filename will be appended to message text. " +
                "Service messages and bot messages will be excluded from peek by default, add `-sys` flag to include them. "
                "Owner can peek globally (`-all`) or in a specific group (`-g <id>`). Keep in mind that Telegram doesn't send easy to use " +
                "deletion data, so the bot needs to lookup ids and messages in the database, making cross searches. Big peeks, or peeks of very old deletions " +
                "will take some time to complete. For specific searches, use the query (`.q`) command. An offset can be specified with `-o` : if given, " +
                "the most `<offset>` recent messages will be skipped and older messages will be peeked. If multiple userbots are logging into the same database " +
                "(but different collections), you can specify on which collection to peek with `-coll`.",
                public=True, args="[-t] [-g [id] | -all] [-sys] [-o <n>] [<num>]")
@alemiBot.on_message(is_allowed & filterCommand(["peek", "deld", "deleted", "removed"], list(alemiBot.prefixes), options={
    "group" : ["-g", "-group"],
    "offset" : ["-o", "-offset"],
    "collection" : ["-coll", "-collection"]
}, flags=["-t", "-all", "-sys"]))
async def deleted_cmd(client, message): # This is a mess omg
    args = message.command
    show_time = "-t" in args["flags"]
    target_group = message.chat
    include_system = "-sys" in args["flags"]
    offset = int(args["offset"]) if "offset" in args else 0
    coll = EVENTS
    if is_me(message):
        if "-all" in args["flags"]:
            target_group = None
        elif "group" in args:
            if args["group"].isnumeric():
                target_group = await client.get_chat(int(args["group"]))
            else:
                target_group = await client.get_chat(args["group"])
        if "collection" in args:
            coll = DB[args["collection"]]
    limit = 1
    if "arg" in args:
        limit = int(args["arg"])
    lgr.info(f"Peeking {limit} messages")
    asyncio.get_event_loop().create_task( # launch the task async because it may take some time
        lookup_deleted_messages(
            client, message, coll,
            target_group, limit, show_time, include_system, offset
        )
    )

