import random
import asyncio
import subprocess
import traceback

from telethon import events

from util import set_offline, ignore_chat
from util.globals import PREFIX
from util.permission import is_allowed, allow, disallow, serialize, list_allowed

# Delete message immediately after it being sent
@events.register(events.NewMessage(
    pattern=r"(?:.*|)(?:-delme|-delete|-d)(?: |)(?P<time>[0-9]+|)$".format(p=PREFIX), outgoing=True))
async def deleteme(event):
    if event.out:
        print(" [ deleting sent message ]")
        t = event.pattern_match.group("time")
        if t != "":
            await asyncio.sleep(float(t))
        await event.message.delete()
        await set_offline(event.client)

# Delete last X messages sent
@events.register(events.NewMessage(
    pattern=r"{p}(?:purge|wipe|clear)(?: |)(?P<target>@[^ ]+|)(?: |)(?P<number>[0-9]+|)".format(p=PREFIX),
    outgoing=True))
async def purge(event):
    try:
        args = event.pattern_match.groupdict()
        number = 1
        if "number" in args and args["number"] != "":
            try:
                number = int(args["number"])
            except:
                pass # default to 1 on fail

        target = await event.client.get_me() # default to delete only self
        if "target" in args and args["target"] not in { "", "@me" }:
            if args["target"] in [ "@all", "@everyone" ]:
                target = None
            else:
                target = await event.client.get_entity(args["target"])
        print(f" [ purging last {number} message from {args['target']} ]")
        n = 0
        async for message in event.client.iter_messages(await event.get_chat()):
            if target is None or message.sender_id == target.id:
                print(f"[DELETING]> {message.message}")
                await message.delete()
                n += 1
            if n >= number:
                break
    except Exception as e:
        traceback.print_exc()
        event.message.edit(event.message.message + "\n`[!] → ` " + str(e))
    await set_offline(event.client)

# Allow someone
@events.register(events.NewMessage(pattern=r"{p}allow(?: |)(?P<name>[^ ]*)".format(p=PREFIX), outgoing=True))
async def allow_cmd(event):
    user_id = None
    if event.is_reply:
        msg = await event.get_reply_message()
        user_id = (await msg.get_input_sender()).user_id
    else:
        user = await event.client.get_entity(event.pattern_match.group('name'))
        user_id = user.id
    if user_id is not None:
        allow(user_id)
        await event.message.edit(event.raw_text + f"\n` → ` Allowed **{user_id}**") 
    else:
        await event.message.edit(event.raw_text + "\n`[!] → ` No user matched")
    await set_offline(event.client)

# Disallow someone
@events.register(events.NewMessage(pattern=r"{p}(?:revoke|disallow)(?: |)(?P<name>[^ ]*)".format(p=PREFIX), outgoing=True))
async def revoke_cmd(event):
    user_id = None
    if event.is_reply:
        msg = await event.get_reply_message()
        user_id = (await msg.get_input_sender()).user_id
    else:
        user = await event.client.get_entity(event.pattern_match.group('name'))
        user_id = user.id
    if user_id is not None:
        disallow(user_id)
        await event.message.edit(event.raw_text + f"\n` → ` Disallowed **{user_id}**") 
    else:
        await event.message.edit(event.raw_text + "\n`[!] → ` No user matched")
    await set_offline(event.client)

# List trusted
@events.register(events.NewMessage(pattern=r"{p}trusted".format(p=PREFIX), outgoing=True))
async def trusted_list(event):
    users = list_allowed()
    text = "[ "
    for u in users:
        try:
            text += (await event.client.get_entity(int(u))).username + " "
        except:
            traceback.print_exc()
            text += "{???} "
    text += "]"
    await event.message.edit(event.raw_text + f"\n` → Allowed Users : `\n{text}") 
    await set_offline(event.client)

class ManagementModules:
    def __init__(self, client):
        self.helptext = "`━━┫ MANAGE `\n"

        client.add_event_handler(purge)
        self.helptext += "`→ .purge [target] [number] ` delete last <n> messages\n"

        client.add_event_handler(allow_cmd)
        self.helptext += "`→ .allow [user] ` add an user as allowed to use bot\n"

        client.add_event_handler(revoke_cmd)
        self.helptext += "`→ .revoke [user] ` remove user permissions to use bot\n"

        client.add_event_handler(trusted_list)
        self.helptext += "`→ .trusted ` list users allowed to run pub cmds\n"

        client.add_event_handler(deleteme)
        self.helptext += "`→ ... -delme [time] ` delete msg ending with `-delme`\n"

        print(" [ Registered Management Modules ]")
