import asyncio
import traceback
import time
import re

from pyrogram import filters

from bot import alemiBot

from termcolor import colored

from util.permission import is_allowed, is_superuser, allow, disallow, serialize, list_allowed, ALLOWED
from util.user import get_username
from util.message import edit_or_reply, get_text, is_me
from util.text import split_for_window
from util.command import filterCommand
from util.time import parse_timedelta
from plugins.help import HelpCategory

import logging
logger = logging.getLogger(__name__)

HELP = HelpCategory("MANAGEMENT")

HELP.add_help("delme", "immediately delete message",
                "add `-delme` at the end of a message to have it deleted after a time. " +
                "If no time is given, message will be immediately deleted", args="[<time>]")
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"(?:.*|)(?:-delme)(?: |)(?P<time>[0-9]+|)$"
), group=5)
async def deleteme(client, message):
    logger.info("Deleting sent message")
    t = message.matches[0]["time"]
    if t != "":
        await asyncio.sleep(float(t))
    await message.delete()

async def get_user(arg, client):
    if arg.isnumeric():
        return await client.get_users(int(arg))
    else:
        return await client.get_users(arg)

HELP.add_help(["purge", "wipe", "clear"], "batch delete messages",
                "delete last <n> sent messages (excluding this) from <targets> (can be more than one). If <n> is not given, will default to 1. " +
                "If no target is given, messages from author of replied msg or self msgs will be deleted. You can give flag `-all` to delete from everyone. " +
                "A keyword (regex) can be specified (`-k`) so that only messages matching given pattern will be deleted. " +
                "An offset can be specified with `-o`, to start deleting after a specific number of messages. " +
                "A time frame can be given: you can limit deletion to messages before (`-before`) a certain time " +
                "(all messages from now up to <time> ago), or after (`-after`) a certain interval (all messages older than <time>). " +
                "Time can be given as a packed string like this : `8y3d4h15m3s` (years, days, hours, minutes, seconds), " +
                "any individual token can be given in any position and all are optional, it can just be `30s` or `5m`. If " +
                "you want to include spaces, wrap the 'time' string in `\"`. If you need to purge messages from an user without an @username, " +
                "you can give its user id with the `-id` flag. If you need to provide more than 1 id, wrap them in `\"` and separate with a space.",
                args="[-k <keyword>] [-o <n>] [-before <time>] [-after <time>] [-all] [-id <ids>] [<targets>] [<number>]", public=False)
@alemiBot.on_message(is_superuser & filterCommand(["purge", "wipe", "clear"], list(alemiBot.prefixes), options={
    "keyword" : ["-k", "-keyword"],
    "offset" : ["-o", "-offset"],
    "ids" : ["-id"],
    "before" : ["-before"],
    "after" : ["-after"]
}, flags=["-all"]))
async def purge(client, message):
    args = message.command
    target = []
    opts = {}
    number = 1
    delete_all = "-all" in args["flags"]
    keyword = re.compile(args["keyword"]) if "keyword" in args else None
    offset = int(args["offset"]) if "offset" in args else 0
    time_limit = time.time() - parse_timedelta(args["before"]).total_seconds() if \
                "before" in args else None
    if "after" in args:
        opts["offset_date"] = int(time.time() - parse_timedelta(args["after"]).total_seconds())
    try:
        if "cmd" in args:
            for a in args["cmd"]:
                if a.startswith("@"):
                    if a == "@me":
                        target.append(message.from_user.id)
                    else:
                        target.append((await get_user(a, client)).id)
                elif a.isnumeric():
                    number = int(a)
        if "ids" in args:
            for single_id in args["ids"].split():
                target.append(int(single_id))
        
        if not target:
            if message.reply_to_message:
                target.append(message.reply_to_message.from_user.id)
            else:
                target.append(message.from_user.id)

        logger.info(f"Purging last {number} message from {target}")
        n = 0
        async for msg in client.iter_history(message.chat.id, **opts):
            if msg.message_id == message.message_id: # ignore message that triggered this
                continue
            if ((delete_all or msg.from_user.id in target)
            and (keyword is None or keyword.search(get_text(msg)))): # wait WTF why no raw here
                if offset > 0: # do an offset like this because
                    offset -=1 #  we want to offset messages from target user, not all messages
                    continue
                await msg.delete()
                n += 1
            if n >= number:
                break
            if time_limit is not None and msg.date < time_limit:
                break
        await edit_or_reply(message, "` → ` Done")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["merge"], "join multiple messages into one",
                "join multiple messages sent by you into one. Reply to the first one to merge, bot will join " +
                "every consecutive message you sent. You can stop the bot from deleting merged messages with " +
                "`-nodel` flag. You can specify a separator with `-s`, it will default to `,`. You can specify max " +
                "number of messages to merge with `-max`.", args="[-s <sep>] [-max <n>] [-nodel]", public=False)
@alemiBot.on_message(is_superuser & filterCommand(["merge"], list(alemiBot.prefixes), options={
    "separator" : ["-s"],
    "max" : ["-max"]
}, flags=["-nodel"]))
async def merge_cmd(client, message):
    if not message.reply_to_message:
        return await edit_or_reply(message, "`[!] → ` No start message given")
    m_id = message.reply_to_message.message_id
    sep = message.command["separator"] if "separator" in message.command else ","
    del_msg = "-nodel" not in message.command["flags"]
    max_to_merge = message.command["max"] if "max" in message.command else -1
    try:
        logger.info(f"Merging messages")
        out = ""
        count = 0
        async for msg in client.iter_history(message.chat.id, offset_id=m_id, reverse=True):
            if not is_me(msg) or (max_to_merge > 0 and count >= max_to_merge):
                break
            out += msg.text.markdown + sep + " "
            count += 1
            if del_msg and msg.message_id != m_id: # don't delete the one we want to merge into
                await msg.delete()
        await message.reply_to_message.edit(out)
        await edit_or_reply(message, f"` → ` Merged {count} messages")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))
    await client.set_offline()

HELP.add_help(["allow", "disallow", "revoke"], "allow/disallow to use bot",
                "this command will work differently if invoked with `allow` or with `disallow`. Target user " +
                "will be given/revoked access to public bot commands. ~~Use `@here` or `@everyone` to allow " +
                "all users in this chat.", args="<target>")
@alemiBot.on_message(is_superuser & filterCommand(["allow", "disallow", "revoke"], list(alemiBot.prefixes)))
async def manage_allowed_cmd(client, message):
    try:
        users_to_manage = []
        if message.reply_to_message is not None:
            peer = message.reply_to_message.from_user
            if peer is None:
                return
            users_to_manage.append(peer)
        elif "cmd" in message.command:
            if message.command["cmd"][0] in ["@here", "@everyone"]:
                async for u in client.iter_chat_members(message.chat.id):
                    if u.user.is_bot:
                        continue
                    users_to_manage.append(u.user)
            else:
                user = None
                try:
                    user = await client.get_users(message.command["cmd"][0])
                except ValueError:
                    return await edit_or_reply(message, "`[!] → ` No user matched")
                if user is None:
                    return await edit_or_reply(message, "`[!] → ` No user matched")
                users_to_manage.append(user)
        else:
            return await edit_or_reply(message, "`[!] → ` Provide an ID or reply to a msg")
        logger.info("Changing permissions")
        out = ""
        action_allow = message.command["base"] == "allow"
        for u in users_to_manage:
            u_name = get_username(u)
            if action_allow:
                if allow(u.id, val=u_name):
                    out += f"` → ` Allowed **{u_name}**\n"
            else:
                if disallow(u.id, val=u_name):
                    out += f"` → ` Disallowed **{u_name}**\n"
        if out != "":
            await edit_or_reply(message, out)
        else:
            await edit_or_reply(message, "` → ` No changes")
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, f"`[!] → ` __{str(e)}__")

HELP.add_help(["trusted", "plist", "permlist"], "list allowed users",
                "note that users without a username may give issues. Use `-s` to get " +
                "the users individually if a batch request fails with 'InvalidPeerId'.", args="[-s]")
# broken af lmaooo TODO
@alemiBot.on_message(is_superuser & filterCommand(["trusted", "plist", "permlist"], list(alemiBot.prefixes), flags=["-s"]))
async def trusted_list(client, message):
    try:
        user_ids = list_allowed()
        text = "`[` "
        issues = ""
        users = []
        logger.info("Listing allowed users")
        if "-s" in message.command["flags"]:
            for uid in list_allowed():
                try:
                    users.append(await client.get_users(uid))
                except:
                    issues += f"~~[{uid}]~~ "
        else:
            users = await client.get_users([ int(u) for u in user_ids ]) # this thing gives a PeerIdInvalid exc???
        for u in users:
            text += f"{get_username(u)}, "
        text += "`]`"
        await edit_or_reply(message, f"` → Allowed Users : `\n{text}\n{issues}") 
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, f"`[!] → ` __{str(e)}__")
