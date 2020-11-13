import asyncio
import subprocess
import time

from termcolor import colored

from telethon import events

from util import can_react, set_offline, batchify
from util.parse import cleartermcolor
from util.globals import PREFIX

last_group = "N/A"

class MessageEntry:
    def __init__(self, channel, author, message, media=False):
        self.channel = channel
        self.author = author
        self.message = message
        self.media = media

    def print_formatted(self):
        global last_group
        if self.channel != last_group:
            print(colored("━━━━━━━━━━┫ " + self.channel, 'magenta', attrs=['bold']))
        last_group = self.channel
        pre = len(self.author) + 3
        text = self.message.replace("\n", "\n" + " "*pre)
        if self.media:
            text = "[+MEDIA] " + text
        text = ("\n" + " "*pre).join(batchify(text, 50)) # 
        print(f"{colored(self.author, 'cyan')} {colored('→', 'grey')} {self.message}")
        
async def parse_event(event, edit=False):
    chat = await event.get_chat()
    author = "UNKNOWN"
    chan = "UNKNOWN"
    msg = event.raw_text
    if edit:
        msg = "[EDIT] " + msg
    if hasattr(chat, 'title'):      # check if this is a group but I found
        chan = chat.title           # no better way (for now)
    else:
        chan = (chat.username if chat.username is not None 
                else f"{chat.first_name}" + (f" {chat.last_name}" if
                    chat.last_name is not None else f"{chat.first_name}"))

    peer = await event.get_input_sender()
    if peer is None:
        author = chan
    else:
        sender = await event.client.get_entity(peer)
        if sender is None:
            author = chan
        elif sender.username is None:
            author = (sender.first_name + ' ' + sender.last_name if
                        sender.last_name is not None else sender.first_name)
        else:
            author = "@" + sender.username
    return MessageEntry(chan, author, msg, media=event.message.media is not None)

# Print in terminal received edits
@events.register(events.MessageEdited)
async def editlogger(event):
    msg = await parse_event(event, edit=True)
    msg.print_formatted()

# This is super lazy but will do for now ig

# Print in terminal received chats
@events.register(events.NewMessage)
async def msglogger(event):
    msg = await parse_event(event)
    msg.print_formatted()

class LoggerModules:
    def __init__(self, client, limit=False):
        self.helptext = ""

        client.add_event_handler(editlogger)
        client.add_event_handler(msglogger)

        print(" [ Registered Logger Modules ]")
