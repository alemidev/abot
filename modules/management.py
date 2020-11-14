import random
import asyncio
import subprocess
import traceback

from telethon import events

from util import can_react, set_offline, ignore_chat
from util.globals import PREFIX

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

# Set chat as ignored for a while
@events.register(events.NewMessage(pattern=r"{p}ignore (?P<seconds>[0-9]+)".format(p=PREFIX), outgoing=True))
async def ignore(event):
    try:
        number = int(event.pattern_match.group(1))
        print(f" [ muting chat ]")
        ignore_chat(event.chat_id, number)
    except: pass

class ManagementModules:
    def __init__(self, client):
        self.helptext = "`━━┫ MANAGE `\n"

        client.add_event_handler(purge)
        self.helptext += "`→ .purge [target] [number] ` delete last <n> messages *\n"

        client.add_event_handler(ignore)
        self.helptext += "`→ .ignore <seconds> ` ignore commands in this chat *\n"

        client.add_event_handler(deleteme)
        self.helptext += "`→ ... -delme [time] ` delete msg ending with `-delme` *\n"

        print(" [ Registered Management Modules ]")
