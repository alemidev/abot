import asyncio

from bot import alemiBot

from pyrogram import filters

from util.message import get_text

# Save file
@alemiBot.on_message(filters.me & filters.command("put", prefixes="."))
async def upload(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = message.reply_to_message
    if msg.media:
        try:
            fpath = await client.download_media(msg)
            await message.edit(get_text(message) + '\n` → ` saved file as {}'.format(fpath))
        except Exception as e:
            await message.edit(get_text(message) + "\n`[!] → ` " + str(e))
    else:
        await message.edit(get_text(message) + "\n`[!] → ` you need to attach or reply to a file, dummy")

# Save file
@alemiBot.on_message(filters.me & filters.command("get", prefixes="."))
async def download(client, message):
    if len(message.command) < 2:
        return await message.edit(message.text + "\n`[!] → ` No filename provided")
    try:
        name = message.command[1]
        await client.send_document(message.chat.id, name, reply_to_message_id=message.message_id, caption=f'` → {name}`')
    except Exception as e:
        await message.edit(message.text + "\n`[!] → ` " + str(e))

# class FilesModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ FILES `\n"
# 
#         client.add_event_handler(upload)
#         self.helptext += "`→ .put ` save attached file to server\n"
# 
#         client.add_event_handler(download)
#         self.helptext += "`→ .get <name> ` upload a file from server to chat\n"
# 
#         print(" [ Registered Files Modules ]")
