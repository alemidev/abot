# alemibot v0.3
### Join [the help channel](https://t.me/alemibothelp)

My personal Telegram userbot. This bot can provide, out of the box, some 
math/moderation/meme/textediting commands. The most relevant features come 
with access to a MongoDB, where messages can be stored. With message caching, 
the bot can provide edit history and show deleted messages.

This project started using Telethon but I migrated to Pyrogram. You can find a `telethon` branch, 
but it won't receive any more support. All features work and it's pretty polished, but the pyro branch 
will receive much more work on.

## Features
* Fully modular : core is minimal, with handy utils. Install the plugins you need!
* `alemigliardi/alemibot-tricks` is a collection of fun to have commands
* `alemigliardi/alemibot-moderation` has some powerful deletion tools
* `alemigliardi/alemibot-debugtool` contains some handy commands to manage your bot and server
# How to deploy
You just need Python 3.7+ and a PC always on to run this. More dependancies will depend on modules.
It is strongly recommended to install this on a UNIX system. If you plan to install on Windows, 
[I recommend installing inside a WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* Clone this repo : `git clone https://github.com/alemigliardi/alemibot.git`
* Make a `venv` with `python3 -m venv <anyfolder>`
* Activate `venv` with `source <venvfolder>/bin/activate`
* Install required libraries with `pip install -r requirements.txt`
* Edit the `config.ini` file with your API hash and ID (visit https://my.telegram.org/)
* Run bot : `python bot.py`. First time it will request your phone number and a verification code.

## config file
The defualt config contains the usable fields already. You just need to fill in `api_id` and `api_hash`.