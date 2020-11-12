import asyncio
import subprocess

from termcolor import colored

from telethon import events

from util import can_react, set_offline, batchify

last_group = "N/A"

def print_if_different(chan):
    global last_group
    if chan != last_group:
        print(colored("━━━━━━━━━━┫ " + chan, 'magenta', attrs=['bold']))
    last_group = chan

# Print in terminal received chats
@events.register(events.NewMessage)
async def printer(event):
    sender = await event.client.get_entity(await event.get_input_sender())
    chan = "UNKNOWN"
    chat = await event.get_chat()   # checking the title is a shit way to
    if hasattr(chat, 'title'):      # check if this is a group but I found
        chan = chat.title           # no better way (for now)
    else:
        chan = (chat.username if chat.username is not None 
                else f"{chat.first_name}" + (f" {chat.last_name}" if
                    chat.last_name is not None else ""))
    print_if_different(chan)
    if sender.username is None:
        author = sender.first_name + ' ' + sender.last_name
    else:
        author = "@" + sender.username
    pre = len(author) + 3
    text = event.raw_text.replace("\n", "\n" + " "*pre)
    if event.message.media is not None:
        text = "[+MEDIA] " + text
    text = ("\n" + " "*pre).join(batchify(text, 50))
    print(f"{colored(author, 'cyan')} {colored('→', 'grey')} {text}")

# Run command
@events.register(events.NewMessage(pattern=r"\.run (.*)"))
async def runit(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        try:
            args = event.pattern_match.group(1)
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
    def __init__(self, client):
        self.helptext = ""

        client.add_event_handler(printer)

        client.add_event_handler(runit)
        self.helptext += "`→ .run <command> ` execute command on server *\n"

        print(" [ Registered System Modules ]")
