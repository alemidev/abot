import time
import json

from telethon.tl.functions.account import UpdateStatusRequest

recent_reacts = {}
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

def can_react(chat_id):
    if chat_id not in recent_reacts:
        recent_reacts[chat_id] = time.time()
        return True
    # Get the time when we last sent a reaction (or 0)
    last = recent_reacts[chat_id]

    # Get the current time
    now = time.time()

    # If <COOLDOWN> seconds have passed, we can react
    if now - last > config['cooldown']:
        # Make sure we updated the last reaction time
        recent_reacts[chat_id] = now
        return True
    else:
        return False

def ignore_chat(chat_id, seconds):
    recent_reacts[chat_id] = time.time() + seconds

async def set_offline(client):
    await client(UpdateStatusRequest(offline=True))

