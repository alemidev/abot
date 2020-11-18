import asyncio
import subprocess
import traceback

from pyrogram import filters

from bot import alemiBot

from termcolor import colored

from util.permission import is_allowed, allow, disallow, serialize, list_allowed, ALLOWED
from util.user import get_username
from util.message import edit_or_reply
from util.text import split_for_window

# Delete message immediately after it being sent
@alemiBot.on_message(filters.me & filters.regex(pattern=
    r"(?:.*|)(?:-delme|-delete|-d)(?: |)(?P<time>[0-9]+|)$"
), group=5)
async def deleteme(_, message):
    print(" [ deleting sent message ]")
    t = message.matches[0]["time"]
    if t != "":
        await asyncio.sleep(float(t))
    await message.delete()

# Delete last X messages sent
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
                target = (await client.get_users(args["target"])).id
        print(f" [ purging last {number} message from {args['target']} ]")
        n = 0
        async for message in client.iter_history(message.chat.id):
            if target is None or message.from_user.id == target:
                print(colored("[DELETING] → ", "red", attrs=["bold"]) + split_for_window(message.text, offset=13))
                await message.delete()
                n += 1
            if n >= number:
                break
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Allow someone
@alemiBot.on_message(filters.me & filters.command(["allow", "disallow", "revoke"], prefixes="."))
async def manage_allowed_cmd(_, message):
    users_to_manage = []
    if event.reply_to_message is not None:
        peer = event.reply_to_message.from_user
        if peer is None:
            return
        users_to_manage.append(peer)
    # elif event.pattern_match.group("name") in [ "@here", "@everyone" ]:
    #     users_to_allow += await event.client.get_participants(await event.get_chat())
    elif len(message.command) > 1:
        user = None
        try:
            user = await alemiBot.get_users(message.command[1])
        except ValueError:
            return await message.edit(message.text + "\n`[!] → ` No user matched")
        if user is None:
            return await message.edit(message.text + "\n`[!] → ` No user matched")
        users_to_manage.append(user)
    else:
        return await message.edit(message.text + "\n`[!] → ` Provide an ID or reply to a msg")
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
        await message.edit(message.text + "\n" + out)
    else:
        await message.edit(message.text + "\n` → ` No changes")

# List trusted
# broken af lmaooo TODO
@alemiBot.on_message(filters.me & filters.command(["trusted", "plist", "permlist"], prefixes="."))
async def trusted_list(c, message):
    user_ids = list_allowed()
    text = "`[` "
    users = await c.get_users([ int(u) for u in user_ids ]) # this thing gives a PeerIdInvalid exc???
    for u in users:
        text += f"{get_username(e)}, "
    text += "`]`"
    await message.edit(message.text + f"\n` → Allowed Users : `\n{text}") 

# class ManagementModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ MANAGE `\n"
# 
#         client.add_event_handler(purge)
#         self.helptext += "`→ .purge [target] [number] ` delete last <n> messages\n"
# 
#         client.add_event_handler(allow_cmd)
#         self.helptext += "`→ .allow [user] ` add an user as allowed to use bot\n"
# 
#         client.add_event_handler(revoke_cmd)
#         self.helptext += "`→ .revoke [user] ` remove user permissions to use bot\n"
# 
#         client.add_event_handler(trusted_list)
#         self.helptext += "`→ .trusted [-i] ` list users allowed to run pub cmds\n"
# 
#         client.add_event_handler(deleteme)
#         self.helptext += "`→ ... -delme [time] ` delete msg ending with `-delme`\n"
# 
#         print(" [ Registered Management Modules ]")
