import asyncio
import traceback

from pyrogram import filters

from bot import alemiBot

from termcolor import colored

from util.permission import is_allowed, is_superuser, allow, disallow, serialize, list_allowed, ALLOWED
from util.user import get_username
from util.message import edit_or_reply, get_text
from util.text import split_for_window
from util.command import filterCommand
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
                "delete last <n> sent messages from <target> (`-t`), excluding this one. If <n> is not given, will default to 1. " +
                "If no target is given, only self messages will be deleted. Target can be `@all` and `@everyone`. " +
                "A keyword can be specified (`-k`) so that only messages containing that keyword will be deleted. " +
                "An offset can be specified with `-o`, to start deleting after a specific number of messages.",
                args="[-t <target>] [-k <keyword>] [-o <n>] [<number>]", public=False)
@alemiBot.on_message(is_superuser & filterCommand(["purge", "wipe", "clear"], list(alemiBot.prefixes), options={
    "target" : ["-t", "-target"],
    "keyword" : ["-k", "-keyword"],
    "offset" : ["-o", "-offset"]
}))
async def purge(client, message):
    args = message.command
    target = message.from_user.id
    number = 1
    keyword = args["keyword"] if "keyword" in args else None
    offset = int(args["offset"]) if "offset" in args else 0

    try:
        if "arg" in args:
            if args["cmd"][0].startswith("@"): # this to support older cmd usage
                tgt = args["cmd"][0]
                if tgt == "@me":
                    pass
                elif tgt in { "@all", "@everyone" }:
                    target = None
                else:
                    target = (await get_user(tgt, client)).id
                if args["cmd"][1] != "-delme":
                    number = int(args["cmd"][1])
            elif args["cmd"][0] != "-delme":
                number = int(args["cmd"][0])

        if "target" in args:
            if args["target"] == "@me":
                pass
            elif args["target"] in { "@all", "@everyone" }:
                target = None
            else:
                target = (await get_user(args["target"], client)).id

        logger.info(f"Purging last {number} message from {target}")
        n = 0
        async for msg in client.iter_history(message.chat.id):
            if msg.message_id == message.message_id: # ignore message that triggered this
                continue
            if ((target is None or msg.from_user.id == target)
            and (keyword is None or keyword in get_text(msg))): # wait WTF why no raw here
                if offset > 0:
                    offset -=1
                    continue
                await msg.delete()
                n += 1
            if n >= number:
                break
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
