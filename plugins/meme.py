import secrets
import random
import asyncio
import os
import traceback
import io

from PIL import Image, ImageEnhance, ImageOps

from pyrogram import filters

from bot import alemiBot

from util import batchify
from util.permission import is_allowed
from util.message import edit_or_reply, get_text

# Get random meme from memes folder
@alemiBot.on_message(is_allowed & filters.command("meme", prefixes=".") & filters.regex(pattern=
    r"meme(?: |$)(?P<list>-list|-l|)(?: |$ |)(?P<name>[^ ]*)"
))
async def getmeme(client, message):
    try:
        args = message.matches[0]
        if args["list"] == "-l" or args["list"] == "-list":
            print(" [ getting meme list ]")
            memes = os.listdir("data/memes")
            memes.sort()
            out = f"` → ` **Meme list** ({len(memes)} total) :\n[ "
            out += ", ".join(memes)
            out += "]"
            await edit_or_reply(out)
        elif args["name"] != "":
            print(f" [ getting specific meme : \"{args['name']}\" ]")
            memes = [ s for s in os.listdir("data/memes")      # I can't decide if this
                        if s.lower().startswith(args["name"])] #  is nice or horrible
            if len(memes) > 0:
                fname = memes[0]
                print(f" [ getting specific meme : \"{fname}\" ]")
                await client.send_document(message.chat.id, "data/memes/"+fname, reply_to_message_id=message.message_id,
                                            caption='` → ` **{}**'.format(fname))
            else:
                await edit_or_reply(f"`[!] → ` no meme named {args['name']}")
        else: 
            fname = secrets.choice(os.listdir("data/memes"))
            print(f" [ getting random meme : \"{fname}\" ]")
            await client.send_photo(message.chat.id, "data/memes/"+fname, reply_to_message_id=message.message_id,
                                        caption='` → Random meme : ` **{}**'.format(fname))
    except Exception as e:
        traceback.print_exc()
        await edit_or_reply(message, "`[!] → ` " + str(e))

# Save a meme
@alemiBot.on_message(filters.me & filters.command("steal", prefixes="."))
async def steal(client, message):
    # if len(message.command) < 2:
    #     return await message.edit(message.text + "\n`[!] → ` No meme name provided")
    msg = message
    if message.reply_to_message is not None:
        msg = message.reply_to_message
    if msg.media:
        try:                                                # TODO I need to get what file type it is!
            fpath = await client.download_media(msg, file_name="data/memes/") # + message.command[1])
            await message.edit(get_text(message) + '\n` → ` saved meme as {}'.format(fpath))
        except Exception as e:
            await message.edit(get_text(message) + "\n`[!] → ` " + str(e))
    else:
        await message.edit(get_text(message) + "\n`[!] → ` you need to attach or reply to a file, dummy")

#
# This is from https://github.com/Ovyerus/deeppyer
#   I should do some license stuff here but TODO
#

async def fry_image(img: Image) -> Image:
    colours = ( # TODO tweak values
        (random.randint(50, 200), random.randint(40, 170), random.randint(40, 190)),
        (random.randint(190, 255), random.randint(170, 240), random.randint(180, 250))
    )

    img = img.copy().convert("RGB")

    # Crush image to hell and back
    img = img.convert("RGB")
    width, height = img.width, img.height
    img = img.resize((int(width ** random.uniform(0.8, 0.9)), int(height ** random.uniform(0.8, 0.9))), resample=Image.LANCZOS)
    img = img.resize((int(width ** random.uniform(0.85, 0.95)), int(height ** random.uniform(0.85, 0.95))), resample=Image.BILINEAR)
    img = img.resize((int(width ** random.uniform(0.89, 0.98)), int(height ** random.uniform(0.89, 0.98))), resample=Image.BICUBIC)
    img = img.resize((width, height), resample=Image.BICUBIC)
    img = ImageOps.posterize(img, random.randint(3, 7))

    # Generate colour overlay
    overlay = img.split()[0]
    overlay = ImageEnhance.Contrast(overlay).enhance(random.uniform(1.0, 2.0))
    overlay = ImageEnhance.Brightness(overlay).enhance(random.uniform(1.0, 2.0))

    overlay = ImageOps.colorize(overlay, colours[0], colours[1])

    # Overlay red and yellow onto main image and sharpen the hell out of it
    img = Image.blend(img, overlay, random.uniform(0.1, 0.4))
    img = ImageEnhance.Sharpness(img).enhance(random.randint(5, 300))

    return img

# DeepFry a meme
@alemiBot.on_message(is_allowed & filters.command("fry", prefixes=".") & filters.regex(pattern=
    r"fry(?: |)(?P<count>-c [0-9]+|)"
))
async def deepfry(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = message.reply_to_message
    if msg.media:
        print(f" [ frying meme ]")
        try:
            count = 1
            if message.matches[0]["count"] != "":
                count = int(message.matches[0]["count"].replace("-c ", ""))
            if message.from_user is not None and message.from_user.is_self: # lmao these checks, just message.outgoing doesn't work in self msgs
                await message.edit(message.text + "\n` → ` Downloading...")
            fpath = await client.download_media(msg, file_name="tofry")
            if message.from_user is not None and message.from_user.is_self:
                await message.edit(message.text + "\n` → ` Downloading [OK]\n` → ` Frying...")
            image = Image.open(fpath)
    
            for _ in range(count):
                image = await fry_image(image)
            if message.from_user is not None and message.from_user.is_self:
                await message.edit(message.text +
                    "\n` → ` Downloading [OK]\n` → ` Frying [OK]\n` → ` Uploading...")
    
            fried_io = io.BytesIO()
            fried_io.name = "fried.jpeg"
            image.save(fried_io, "JPEG")
            fried_io.seek(0)
            await client.send_photo(message.chat.id, fried_io, reply_to_message_id=message.message_id,
                                        caption=f"` → Fried {count} time{'s' if count > 1 else ''}`")
            if message.from_user is not None and message.from_user.is_self:
                await message.edit(message.text +
                    "\n` → ` Downloading [OK]\n` → ` Frying [OK]\n` → ` Uploading [OK]")
        except Exception as e:
            await message.edit(get_text(message) + "\n`[!] → ` " + str(e))
    else:
        await message.edit(get_text(message) + "\n`[!] → ` you need to attach or reply to a file, dummy")

#
#   This comes from https://github.com/anuragrana/Python-Scripts/blob/master/image_to_ascii.py
#

def ascii_image(img:Image) -> str:
    # resize the image
    width, height = img.size
    aspect_ratio = height/width
    new_width = 120
    new_height = aspect_ratio * new_width * 0.55
    img = img.resize((new_width, int(new_height)))
    img = img.convert('L')
    
    pixels = img.getdata()
    
    # replace each pixel with a character from array
    chars = ["B","S","#","&","@","$","%","*","!",":","."]
    new_pixels = [chars[pixel//25] for pixel in pixels]
    new_pixels = ''.join(new_pixels)
    
    # split string of chars into multiple strings of length equal to new width and create a list
    new_pixels_count = len(new_pixels)
    ascii_image = [new_pixels[index:index + new_width] for index in range(0, new_pixels_count, new_width)]
    ascii_image = "\n".join(ascii_image)
    return ascii_image

# Make ASCII art of an image
@alemiBot.on_message(is_allowed & filters.command("ascii", prefixes="."))
async def ascii_cmd(client, message):
    msg = message
    if message.reply_to_message is not None:
        msg = message.reply_to_message
    if msg.media:
        print(f" [ making ascii of img ]")
        try:
            fpath = await client.download_media(msg, file_name="toascii")
            image = Image.open(fpath)
            
            out = io.BytesIO(ascii_image(image).encode('utf-8'))
            out.name = "ascii.txt"

            await client.send_document(message.chat.id, out, reply_to_message_id=message.message_id,
                                        caption=f"` → Made ASCII art `")
        except Exception as e:
            traceback.print_exc()
            await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    else:
        await event.message.edit(event.raw_text + 
                "\n`[!] → ` you need to attach or reply to a file, dummy")

# class MemeModules:
#     def __init__(self, client):
#         self.helptext = "`━━┫ MEME `\n"
# 
#         client.add_event_handler(getmeme)
#         self.helptext += "`→ .meme [-list] [name]` get a meme *\n"
# 
#         client.add_event_handler(steal)
#         self.helptext += "`→ .steal <name> ` add meme to collection\n"
# 
#         client.add_event_handler(deepfry)
#         self.helptext += "`→ .fry [-c n] ` fry a meme n times *\n"
# 
#         client.add_event_handler(ascii_cmd)
#         self.helptext += "`→ .ascii ` make ascii art from img *\n"
# 
#         print(" [ Registered Meme Modules ]")
