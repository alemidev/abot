import asyncio
import subprocess
import time

from termcolor import colored

from telethon import events

from util import can_react, set_offline, batchify
from util.parse import cleartermcolor
from util.globals import PREFIX

last_group = "N/A"

def print_if_different(chan):
    global last_group
    if chan != last_group:
        print(colored("━━━━━━━━━━┫ " + chan, 'magenta', attrs=['bold']))
    last_group = chan

# Print in terminal received chats
# TODO make this a proper chat logger, for edits and deletes
@events.register(events.NewMessage)
async def printer(event):
    peer = await event.get_input_sender()
    if peer is None:
        sender = None
    else:
        sender = await event.client.get_entity(peer)
    chan = "UNKNOWN"
    chat = await event.get_chat()   # checking the title is a shit way to
    if hasattr(chat, 'title'):      # check if this is a group but I found
        chan = chat.title           # no better way (for now)
    else:
        chan = (chat.username if chat.username is not None 
                else f"{chat.first_name}" + (f" {chat.last_name}" if
                    chat.last_name is not None else ""))
    print_if_different(chan)
    if sender is None:
        author = chan
    elif sender.username is None:
        author = sender.first_name + ' ' + sender.last_name
    else:
        author = "@" + sender.username
    pre = len(author) + 3
    text = event.raw_text.replace("\n", "\n" + " "*pre)
    if event.message.media is not None:
        text = "[+MEDIA] " + text
    text = ("\n" + " "*pre).join(batchify(text, 50))
    print(f"{colored(author, 'cyan')} {colored('→', 'grey')} {text}")

# Repy to .asd with "a sunny day" (and calculate ping)
@events.register(events.NewMessage(pattern=r"{p}asd".format(p=PREFIX)))
async def ping(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        msg = event.raw_text
        before = time.time()
        await event.message.edit(msg + "\n` → ` a sunny day")
        after = time.time()
        latency = (after - before) * 1000
        await event.message.edit(msg + f"\n` → ` a sunny day `({latency:.0f}ms)`")
    await set_offline(event.client)


# Update userbot (git pull + restart)
@events.register(events.NewMessage(pattern=r"{p}update".format(p=PREFIX), outgoing=True))
async def update(event):
    if not can_react(event.chat_id):
        return
    msg = event.raw_text
    try:
        print(f" [ Updating bot ]")
        msg += "\n` → ` Updating"
        await event.message.edit(msg) 
        result = subprocess.run(["git", "pull"], capture_output=True, timeout=60)
        msg += " [OK]\n` → ` Bot will now restart"
        await event.message.edit(msg) 
        await event.client.disconnect()
    except Exception as e:
        msg += " [FAIL]\n`[!] → ` " + str(e)
        await event.message.edit(msg) 
    await set_offline(event.client)

# Run command
@events.register(events.NewMessage(pattern=r"{p}(?:run|r) (?P<cmd>.*)"))
async def runit(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        try:
            args = event.pattern_match.group("cmd")
            print(f" [ running command \"{args}\" ]")
            result = subprocess.run(args, shell=True, capture_output=True, timeout=60)
            output = f"$ {args}\n" + cleartermcolor(result.stdout.decode())
            if len(output) > 4080:
                with open("output", "w") as f:
                    f.write(output) # lmaoooo there must be a better way
                await event.message.reply("``` → Output too long to display```", file="output")
            else:
                await event.message.reply("```" + output + "```")
        except Exception as e:
            await event.message.reply("`[!] → ` " + str(e))
    else:
        await event.message.reply("` → ( ͡° ͜ʖ ͡°)` nice try")
    await set_offline(event.client)

class SystemModules:
    def __init__(self, client, limit=False):
        self.helptext = ""

        if not limit:
            client.add_event_handler(printer)

            client.add_event_handler(runit)
            self.helptext += "`→ .run <cmd> ` execute command on server (`.r`) *\n"

        client.add_event_handler(ping)
        self.helptext += "`→ .asd ` a sunny day (+ get latency) *\n"

        client.add_event_handler(update)
        self.helptext += "`→ .update ` (git) pull changes and reboot bot *\n"


        print(" [ Registered System Modules ]")
