import asyncio
import subprocess
import time
import io
import traceback
import json

from bot import alemiBot

from pyrogram import filters

from util.permission import is_allowed
from util.message import edit_or_reply, is_me
from plugins.help import HelpCategory

HELP = HelpCategory("CORE")

HELP.add_help(["asd", "ping"], "a sunny day!",
                "The ping command.")
@alemiBot.on_message(filters.me & filters.command(["asd", "ping"], list(alemiBot.prefixes)))
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
@alemiBot.on_message(filters.me & filters.command("update", list(alemiBot.prefixes)))
async def update(client, message):
    msg = message.text.markdown
    try:
        print(f" [ Updating bot ]")
        msg += "\n` → ` Updating"
        await message.edit(msg) 
        result = subprocess.run(["git", "pull"], capture_output=True, timeout=60)
        result = subprocess.run(["pip", "install", "-r", "requirements.txt"],
                                                    capture_output=True, timeout=60)
        msg += " [OK]\n` → ` Restarting"
        await message.edit(msg) 
        with open("data/lastmsg.json", "w") as f:
            json.dump({"message_id": message.message_id,
                        "chat_id": message.chat.id}, f)
        asyncio.get_event_loop().create_task(client.restart())
    except Exception as e:
        traceback.print_exc()
        msg += " [FAIL]\n`[!] → ` " + str(e)
        await message.edit(msg) 

HELP.add_help("where", "get info about chat",
                "Get the complete information about current chat and attach as json",
                args="[<target>]", public=True)
@alemiBot.on_message(is_allowed & filters.command("where", list(alemiBot.prefixes)))
async def where_cmd(client, message):
    try:
        tgt = message.chat
        if len(message.command) > 1:
            arg = message.command[1]
            if arg.isnumeric():
                tgt = await client.get_chat(int(arg))
            else:
                tgt = await client.get_chat(arg)
        print(f" [ getting info of chat ]")
        if is_me(message):
            await message.edit(message.text.markdown + f"\n` → ` Getting data of chat `{tgt.id}`")
        out = io.BytesIO((str(tgt)).encode('utf-8'))
        out.name = f"chat-{message.chat.id}.json"
        await client.send_document(message.chat.id, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))

HELP.add_help("who", "get info about user",
                "Get the complete information about an user (replied to or "+
                "id given) and attach as json", public=True, args="[<target>]")
@alemiBot.on_message(is_allowed & filters.command("who", list(alemiBot.prefixes)))
async def who_cmd(client, message):
    try:
        peer = None
        if len(message.command) > 1:
            arg = message.command[1]
            if arg.isnumeric():
                peer = await client.get_users(int(arg))
            else:
                peer = await client.get_users(arg)
        elif message.reply_to_message is not None \
        and message.reply_to_message.from_user is not None:
            peer = message.reply_to_message.from_user
        else:
            peer = await client.get_users(message.from_user)
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
                "Get the complete information about a message (replied to, from specified id or "+
                "the sent message) and attach as json. If no chat is specified, " +
                "message will be searched in current chat", args="[<target> [<chat>]]", public=True)
@alemiBot.on_message(is_allowed & filters.command("what", list(alemiBot.prefixes)))
async def what_cmd(client, message):
    msg = message
    try:
        if message.reply_to_message is not None:
            msg = await client.get_messages(message.chat.id, message.reply_to_message.message_id)
        elif len(message.command) > 1 and message.command[1].isnumeric():
            chat_id = message.chat.id
            if len(message.command) > 2 and message.command[2].isnumeric():
                chat_id = int(message.command[2])
            msg = await client.get_messages(chat_id, int(message.command[1]))
        print(f" [ getting info of msg ]")
        if is_me(message):
            await message.edit(message.text.markdown + f"\n` → ` Getting data of msg `{msg.message_id}`")
        out = io.BytesIO((str(msg)).encode('utf-8'))
        out.name = f"msg-{msg.message_id}.json"
        await client.send_document(message.chat.id, out)
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message,"`[!] → ` " + str(e))
