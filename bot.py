#!/usr/bin/env python
"""
This is still kind of a single file mess, but I'm trying to get the hang of the basics here.
A plugin system with a core launcher is sure the next step in making a proper project.
Also, some of this code comes from telehon examples
"""
import re
import os
import sys
import time
import json
import random
import subprocess

from termcolor import colored

from telethon import TelegramClient, events
from telethon.tl.types import User, Chat
from telethon.tl.functions.account import UpdateStatusRequest

import requests

import wikipedia
import italian_dictionary

from PyDictionary import PyDictionary

dictionary = PyDictionary()

# "When did we last react?"
recent_reacts = {}

last_group = "N/A"
PREFIX = "."
COOLDOWN = 3

config = None

with open("config.json") as f:
    config = json.load(f)

def batchify(str_in, size):
    if len(str_in) < size:
        return [str_in]
    out = []
    for i in range((len(str_in)//size) + 1):
        out.append(str_in[i*size : (i+1)*size])
    return out

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def cleartermcolor(raw_in):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', raw_in)

async def set_offline(client):
    await client(UpdateStatusRequest(offline=True))

def print_if_different(chan):
    global last_group
    if chan != last_group:
        print(colored("━━━━━━━━━━┫ " + chan, 'magenta', attrs=['bold']))
    last_group = chan

def can_react(chat_id):
    if chat_id not in recent_reacts:
        recent_reacts[chat_id] = time.time()
        return True
    # Get the time when we last sent a reaction (or 0)
    last = recent_reacts[chat_id]

    # Get the current time
    now = time.time()

    # If <COOLDOWN> seconds have passed, we can react
    if now - last > COOLDOWN:
        # Make sure we updated the last reaction time
        recent_reacts[chat_id] = now
        return True
    else:
        return False

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
        await event.message.reply("no")
    await set_offline(event.client)

# Get random meme from memes folder
@events.register(events.NewMessage(pattern=r"\.meme"))
async def meme(event):
    if not can_react(event.chat_id):
        return
    try:
        fname = random.choice(os.listdir("memes"))
        await event.message.reply('` → {}`'.format(fname.split(".")[0]), file=("memes/" + fname))
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Save a meme
@events.register(events.NewMessage(pattern=r"\.steal (.*)"))
async def steal(event):
    if not can_react(event.chat_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        if event.out:
            arg = event.pattern_match.group(1).split(" ")[0] # just in case don't allow spaces
            try:
                fname = await event.client.download_media(message=msg, file="memes/"+arg)
                await event.message.reply('` → ` saved meme as {}'.format(fname))
            except Exception as e:
                await event.message.reply("`[!] → ` " + str(e))
        else:
            await event.message.reply("` → ` nah only I can judge good memz")
    else:
        await event.message.reply("` → ` you need to attach a file, dummy")
    await set_offline(event.client)

# Run fortune
@events.register(events.NewMessage(pattern=r"\.fortune"))
async def fortune(event):
    if not can_react(event.chat_id):
        return
    try:
        print(f" [ running command \"fortune\" ]")
        result = subprocess.run("fortune", capture_output=True)
        output = cleartermcolor(result.stdout.decode())
        await event.message.reply("```" + output + "```")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Search on wikipedia
@events.register(events.NewMessage(pattern=r"\.wiki (.*)"))
async def wiki(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1).replace(" ", "")
        print(f" [ searching \"{arg}\" on wikipedia ]")
        page = wikipedia.page(arg)
        out = f"` → {page.title}`\n"
        out += page.content[:750]
        out += f"... {page.url}"
        if len(page.images) > 0:
            try:
                await event.message.reply(out, link_preview=False,
                    file=page.images[0])
            except Exception as e:
                await event.message.reply(out)
        else:
            await event.message.reply(out, link_preview=False)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Search on italian dictionary
@events.register(events.NewMessage(pattern=r"\.diz (.*)"))
async def dizionario(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1)
        print(f" [ searching \"{arg}\" on it dictionary ]")
        # Use this to get only the meaning 
        res = italian_dictionary.get_definition(arg) 

        out = f"` → {res['lemma']} ` [ {' | '.join(res['sillabe'])} ]\n"
        out += f"```{', '.join(res['grammatica'])} - {res['pronuncia']}```\n\n"
        out += "\n\n".join(res['definizione'])
        for m in batchify(out, 4080):
            await event.message.reply(m)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e) if str(e) != "" else "Not found")
    await set_offline(event.client)

# Search on english dictionary
@events.register(events.NewMessage(pattern=r"\.dict (.*)"))
async def diz(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = event.pattern_match.group(1)
        print(f" [ searching \"{arg}\" on eng dictionary ]")
        # Use this to get only the meaning 
        res = dictionary.meaning(arg)
        if res is None:
            return await event.message.reply("` → No match`")
        out = ""
        for k in res:
            out += f"`→ {k} : `"
            out += "\n * "
            out += "\n * ".join(res[k])
            out += "\n\n"
        for m in batchify(out, 4080):
            await event.message.reply(m)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Roll dice
@events.register(events.NewMessage(pattern=r"\.roll (.*)"))
async def roll(event):
    if not can_react(event.chat_id):
        return
    try:
        arg = int(event.pattern_match.group(1).replace("d",""))
        print(f" [ rolling d{arg} ]")
        await event.message.reply(f"` → {random.randint(1, arg)}`")
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Spam message x times
@events.register(events.NewMessage(pattern=r"\.spam " +
                r"([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]) (.*)"))
async def spam(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        try:
            number = int(event.pattern_match.group(1))
            mess = event.pattern_match.group(2)
            print(f" [ spamming \"{mess}\" for {number} times ]")
            for i in range(number):
                await event.respond(mess)
        except Exception as e:
            await event.reply("`[!] → ` " + str(e))
    else:
        await event.reply("` → ` you wish")
    await set_offline(event.client)

# Replace .shrug with shrug emoji (or reply with one)
@events.register(events.NewMessage(pattern=r"\.shrug"))
async def shrug(event):
    if not can_react(event.chat_id):
        return
    print(f" [ ¯\_(ツ)_/¯ ]")
    if event.out:
        await event.message.edit(r'¯\_(ツ)_/¯')
    else:
        await event.reply(r'¯\_(ツ)_/¯')
    await set_offline(event.client)

# Delete message immediately after it being sent
@events.register(events.NewMessage(pattern=r"\.delete"))
async def deleteme(event):
    if event.out:
        print(f" [ deleting last message ]")
        await event.message.delete()
        await set_offline(event.client)

# Register `events.NewMessage` before defining the client.
# Once you have a client, `add_event_handler` will use this event.
@events.register(events.NewMessage)
async def trigger_replies(event):
    # There are better ways to do this, but this is simple.
    # If the message is not outgoing (i.e. someone else sent it)
    chat = await event.get_chat()   # checking the title is a shit way to
    if hasattr(chat, 'title'):      # check if this is a group but I found
        return                      # no better way (for now)
    if len(event.raw_text) > 25: # don't receive triggers from long messages
        return
    if not event.out:
        if 'come stai' in event.raw_text.lower():
            if can_react(event.chat_id):
                await event.reply('probabilmente seduto')

        elif 'cosa fai' in event.raw_text.lower() or 'che fai' in event.raw_text.lower():
            if can_react(event.chat_id):
                await event.reply('schifo')

        elif 'dove sei' in event.raw_text.lower():
            if can_react(event.chat_id):
                await event.reply('un anfiteatro di cazzi tuoi mai proprio')

        elif ' chi ' in event.raw_text.lower():
            if can_react(event.chat_id):
                await event.reply('tua madre')

        elif 'oroscopo' in event.raw_text.lower():
            if can_react(event.chat_id):
                await event.reply("chiaro, l'ho letto tutto")
        await set_offline(event.client)

# Save file
@events.register(events.NewMessage(pattern=r"\.save"))
async def save(event):
    if not can_react(event.chat_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        if event.out:
            try:
                file = await event.client.download_media(message=msg)
                await event.message.reply('` → ` saved file as {}'.format(file))
            except Exception as e:
                await event.message.reply("`[!] → ` " + str(e))
        else:
            await event.message.reply("` → ` nice malware, u can keep it")
    else:
        await event.message.reply("` → ` you need to attach a file, dummy")
    await set_offline(event.client)

# Upload file
@events.register(events.NewMessage(pattern=r"\.upload (.*)"))
async def upload(event):
    if not can_react(event.chat_id):
        return
    if event.out:
        try:
            name = event.pattern_match.group(1)
            await event.message.reply('` → {}`'.format(name), file=name)
        except Exception as e:
            await event.message.reply("`[!] → ` " + str(e))
    else:
        await event.message.reply("` → ` wouldn't you like to know, weather boy?")
    await set_offline(event.client)

# Print in terminal received chats
@events.register(events.NewMessage)
async def printer(event):
    sender = await client.get_entity(await event.get_input_sender())
    chat = await client.get_entity(event.message.peer_id)
    chan = "UNKNOWN"
    if isinstance(chat, User):
        chan = (chat.username if chat.username is not None 
                else f"{chat.first_name}" + (f" {chat.last_name}" if
                    chat.last_name is not None else ""))
    else:
        chan = chat.title
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

# Help message
@events.register(events.NewMessage(pattern=r"\.help"))
async def helper(event):
    if can_react(event.chat_id):
        await event.reply("` ᚨᛚᛖᛗᛁᛒᛟᛏ v0.1` (cmds with * are restricted)\n" +
                          "`→ .help ` print this\n" +
                          "`→ .wiki <something> ` search something on wikipedia\n" +
                          "`→ .diz <something> ` look up something on italian dictionary\n" +
                          "`→ .dict <something> ` look up something on english dictionary\n" +
                          "`→ .shrug ` replace or reply with shrug composite emote\n" +
                          "`→ .roll d<n> ` roll a virtual dice with n faces\n" +
                          "`→ .fortune ` you feel lucky!?\n" +
                          "`→ .delete ` delete sent message immediately *\n" +
                          "`→ .spam <number> <message> ` self explainatory *\n" +
                          "`→ .run <command> ` execute command on server *\n" +
                          "`→ .save ` save attached file to server *\n" +
                          "`→ .upload ` upload a file from server to chat *\n" +
                        "\nhttps://github.com/alemigliardi/alemibot")

client = TelegramClient(
    config["NAME"], config["ID"],
    config["HASH"],
    proxy=None
)

with client:
    client.add_event_handler(trigger_replies)
    client.add_event_handler(printer)
    client.add_event_handler(helper)

    # This remembers the events.NewMessage we registered before
    client.add_event_handler(spam)
    client.add_event_handler(save)
    client.add_event_handler(deleteme)
    client.add_event_handler(upload)
    client.add_event_handler(shrug)
    client.add_event_handler(meme)
    client.add_event_handler(steal)
    client.add_event_handler(fortune)
    client.add_event_handler(wiki)
    client.add_event_handler(dizionario)
    client.add_event_handler(diz)
    client.add_event_handler(roll)
    client.add_event_handler(runit)

    print(' [ Press Ctrl+C to stop this ]\n')
    client.run_until_disconnected()
print()

