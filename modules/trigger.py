import asyncio

from telethon import events

from util import can_react, set_offline

# TODO make user defineable dictionaries

# Reply with stock messages when receiving trigger words
@events.register(events.NewMessage)
async def trigger_replies(event):
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

class TriggerModules:
    def __init__(self, client):
        self.helptext = ""
        client.add_event_handler(trigger_replies)
        print(" [ Registered TriggerEvent Modules ]")
