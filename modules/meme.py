import random
import asyncio
import os
import traceback
import io

from PIL import Image, ImageEnhance, ImageOps

from telethon import events

from util import set_offline, batchify
from util.globals import PREFIX
from util.permission import is_allowed

# Get random meme from memes folder
@events.register(events.NewMessage(
    pattern=r"{p}meme(?: |$)(?P<list>-list|-l|)(?: |$ |)(?P<name>[^ ]*)".format(p=PREFIX)))
async def getmeme(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    try:
        args = event.pattern_match.groupdict()
        if "list" in args and args["list"] in { "-l", "-list" }:
            print(" [ getting meme list ]")
            memes = os.listdir("data/memes")
            memes.sort()
            out = f"` → ` **Meme list** ({len(memes)} total) :\n[ "
            out += ", ".join(memes)
            out += "]"
            for m in batchify(out, 4090):
                await event.message.reply(m)
        elif "name" in args and args["name"] != "":
            print(f" [ getting specific meme : \"{args['name']}\" ]")
            memes = [ s for s in os.listdir("data/memes")      # I can't decide if this
                        if s.lower().startswith(args["name"])] #  is nice or horrible
            if len(memes) > 0:
                fname = memes[0]
                print(f" [ getting specific meme : \"{fname}\" ]")
                await event.message.reply('` → ` **{}**'.format(fname), file=("data/memes/" + fname))
            else:
                await event.message.reply(f"`[!] → ` no meme named {args['name']}")
        else: 
            fname = random.choices(os.listdir("data/memes"))
            print(f" [ getting random meme : \"{fname}\" ]")
            await event.message.reply('` → Random meme : ` **{}**'.format(fname), file=("data/memes/" + fname))
    except Exception as e:
        traceback.print_exc()
        await event.message.reply("`[!] → ` " + str(e))
    await set_offline(event.client)

# Save a meme
@events.register(events.NewMessage(pattern=r"{p}steal (?P<name>[^ ]*)".format(p=PREFIX), outgoing=True))
async def steal(event):
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        arg = event.pattern_match.group("name")
        if arg == "":
            return await event.message.edit(event.raw_text + "\n`[!] → ` you need to provide a name")
        print(f" [ stealing meme as \"{arg}\" ]")
        try:
            fname = await event.client.download_media(message=msg, file="data/memes/"+arg)
            await event.message.edit(event.raw_text +
                '\n` → ` saved meme as {}'.format(fname.replace("data/memes/", "")))
        except Exception as e:
            await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    else:
        await event.message.edit(event.raw_text + 
                "\n`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

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
@events.register(events.NewMessage(pattern=r"{p}fry(?: |)(?P<count>-c [0-9]+|)".format(p=PREFIX)))
async def deepfry(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        print(f" [ frying meme ]")
        try:
            count = 1
            if event.pattern_match.group("count") != "":
                count = int(event.pattern_match.group("count").replace("-c ", ""))
            if event.out:
                await event.message.edit(event.raw_text + "\n` → ` Downloading...")
            image = io.BytesIO()
            await event.client.download_media(message=msg, file=image)
            image = Image.open(image)
    
            if event.out:
                await event.message.edit(event.raw_text + "\n` → ` Downloading [OK]\n` → ` Frying...")
            for _ in range(count):
                image = await fry_image(image)
            if event.out:
                await event.message.edit(event.raw_text +
                    "\n` → ` Downloading [OK]\n` → ` Frying [OK]\n` → ` Uploading...")
    
            fried_io = io.BytesIO()
            fried_io.name = "fried.jpeg"
            image.save(fried_io, "JPEG")
            fried_io.seek(0)
            await event.reply(f"` → Fried {count} time{'s' if count > 1 else ''}`", file=fried_io)
            if event.out:
                await event.message.edit(event.raw_text +
                    "\n` → ` Downloading [OK]\n` → ` Frying [OK]\n` → ` Uploading [OK]")
        except Exception as e:
            traceback.print_exc()
            await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    else:
        await event.message.edit(event.raw_text + 
                "\n`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

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
@events.register(events.NewMessage(pattern=r"{p}ascii".format(p=PREFIX)))
async def ascii_cmd(event):
    if not event.out and not is_allowed(event.sender_id):
        return
    msg = event.message
    if event.is_reply:
        msg = await event.get_reply_message()
    if msg.media is not None:
        print(f" [ making ascii of img ]")
        try:
            image = io.BytesIO()
            await event.client.download_media(message=msg, file=image)
            image = Image.open(image)
            
            out = io.BytesIO(ascii_image(image).encode('utf-8'))
            out.name = "ascii.txt"

            await event.message.reply("` → Made ASCII art `", file=out)
        except Exception as e:
            traceback.print_exc()
            await event.message.edit(event.raw_text + "\n`[!] → ` " + str(e))
    else:
        await event.message.edit(event.raw_text + 
                "\n`[!] → ` you need to attach or reply to a file, dummy")
    await set_offline(event.client)

class MemeModules:
    def __init__(self, client):
        self.helptext = "`━━┫ MEME `\n"

        client.add_event_handler(getmeme)
        self.helptext += "`→ .meme [-list] [name]` get a meme *\n"

        client.add_event_handler(steal)
        self.helptext += "`→ .steal <name> ` add meme to collection\n"

        client.add_event_handler(deepfry)
        self.helptext += "`→ .fry [-c n] ` fry a meme n times *\n"

        client.add_event_handler(ascii_cmd)
        self.helptext += "`→ .ascii ` make ascii art from img *\n"

        print(" [ Registered Meme Modules ]")
