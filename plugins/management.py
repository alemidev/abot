import asyncio
import subprocess
import traceback

from pyrogram import filters

from bot import alemiBot

from termcolor import colored

from util.permission import is_allowed, allow, disallow, serialize, list_allowed, ALLOWED
from util.user import get_username
from util.message import edit_or_reply, get_text
from util.text import split_for_window
from plugins.help import HelpCategory

HELP = HelpCategory("MANAGEMENT")

HELP.add_help("delme", "immediately delete message",
                "add `-delme`, `-delete` or `-del` at the end of a message to have it deleted after a time. " +
                "If no time is given, message will be immediately deleted", args="[time]")
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"(?:.*|)(?:-delme|-delete|-d)(?: |)(?P<time>[0-9]+|)$"
), group=5)
async def deleteme(_, message):
    print(" [ deleting sent message ]")
    t = message.matches[0]["time"]
    if t != "":
        await asyncio.sleep(float(t))
    await message.delete()

HELP.add_help(["purge", "wipe", "clear"], "batch delete messages",
                "delete last <n> sent messages from <target>. If <n> is not given, will default to 1. " +
                "If no target is given, only self messages will be deleted. Target can be `@all` and `@everyone`",
                args="[target] [number]", public=True)
@alemiBot.on_message(is_allowed & filters.regex(pattern=
    r"^[\.\/](?:purge|wipe|clear)(?: |)(?P<target>@[^ ]+|)(?: |)(?P<number>[0-9]+|)"
))
async def purge(client, message):
    try:
        args = message.matches[0]
        number = 1
        if args["number"] != "":
            try:
                number = int(args["number"])
            except:
                pass # default to 1 on fail

        target = message.from_user.id
        if args["target"] != "" and args["target"] != "@me":
            if args["target"] == "@all" or args["target"] == "@everyone":
                target = None
            else:
                try:
                    target = (await client.get_users(int(args["target"]))).id
                except ValueError:
                    target = (await client.get_users(args["target"])).id
        print(f" [ purging last {number} message from {args['target']} ]")
        n = 0
        async for message in client.iter_history(message.chat.id):
            if target is None or message.from_user.id == target:
                print(colored("[DELETING] → ", "red", attrs=["bold"]) + split_for_window(get_text(message), offset=13))
                await message.delete()
                n += 1
            if n >= number:
                break
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

HELP.add_help(["allow", "disallow", "revoke"], "allow/disallow to use bot",
                "this command will work differently if invoked with `allow` or with `disallow`. Target user " +
                "will be given/revoked access to public bot commands. ~~Use `@here` or `@everyone` to allow " +
                "all users in this chat.", args="<target>")
@alemiBot.on_message(filters.me & filters.command(["allow", "disallow", "revoke"], prefixes="."))
async def manage_allowed_cmd(client, message):
    try:
        users_to_manage = []
        if message.reply_to_message is not None:
            peer = message.reply_to_message.from_user
            if peer is None:
                return
            users_to_manage.append(peer)
        elif len(message.command) > 1 and message.command[1] == "@here" \
        or message.command[1] == "@everyone":
            async for u in client.iter_chat_members(message.chat.id):
                if u.is_bot:
                    continue
                users_to_allow.append(u)
        elif len(message.command) > 1:
            user = None
            try:
                user = await client.get_users(message.command[1])
            except ValueError:
                return await message.edit(message.text.markdown + "\n`[!] → ` No user matched")
            if user is None:
                return await message.edit(message.text.markdown + "\n`[!] → ` No user matched")
            users_to_manage.append(user)
        else:
            return await message.edit(message.text.markdown + "\n`[!] → ` Provide an ID or reply to a msg")
        out = ""
        action_allow = message.command[0] == "allow"
        for u in users_to_manage:
            u_name = get_username(u)
            if action_allow:
                if allow(u.id, val=u_name):
                    out += f"` → ` Allowed **{u_name}**\n"
            else:
                if disallow(u.id, val=u_name):
                    out += f"` → ` Disallowed **{u_name}**\n"
        if out != "":
            await message.edit(message.text.markdown + "\n" + out)
        else:
            await message.edit(message.text.markdown + "\n` → ` No changes")
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + f"\n`[!] → ` __{str(e)}__")

HELP.add_help(["trusted", "plist", "permlist"], "list allowed users",
                "note that users without a username may give issues. Use `-s` to get " +
                "the users individually if a batch request fails with 'InvalidPeerId'.", args="[-s]")
# broken af lmaooo TODO
@alemiBot.on_message(filters.me & filters.command(["trusted", "plist", "permlist"], prefixes="."))
async def trusted_list(client, message):
    try:
        user_ids = list_allowed()
        text = "`[` "
        issues = ""
        users = []
        if len(message.command) > 1 and message.command[1] == "-s":
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
        await message.edit(message.text.markdown + f"\n` → Allowed Users : `\n{text}\n{issues}") 
    except Exception as e:
        traceback.print_exc()
        await message.edit(message.text.markdown + f"\n`[!] → ` __{str(e)}__")
