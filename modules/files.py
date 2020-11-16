import asyncio

from telethon import events

from util import can_react, set_offline
from util.globals import PREFIX

# Save file
@events.register(events.NewMessage(pattern=r"{p}put".format(p=PREFIX), outgoing=True))
async def upload(event):
    if not can_react(event.chat_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        try:
            file = await event.client.download_media(message=msg)
            await event.message.reply('` → ` saved file as {}'.format(file))
        except Exception as e:
            await event.message.reply("`[!] → ` " + str(e))
    else:
        await event.message.reply("`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

# Upload file
@events.register(events.NewMessage(pattern=r"{p}get(?: |)(?P<name>[^ ]*)".format(p=PREFIX), outgoing=True))
async def download(event):
    if not can_react(event.chat_id):
        return
    try:
        name = event.pattern_match.group("name")
        await event.message.reply('` → {}`'.format(name), file=name)
    except Exception as e:
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

class FilesModules:
    def __init__(self, client):
        self.helptext = "`━━┫ FILES `\n"

        client.add_event_handler(upload)
        self.helptext += "`→ .put ` save attached file to server\n"

        client.add_event_handler(download)
        self.helptext += "`→ .get <name> ` upload a file from server to chat\n"

        print(" [ Registered Files Modules ]")
