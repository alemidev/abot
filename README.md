# alemibot / ᚨᛚᛖᛗᛁᛒᛟᛏ  v0.3
### Join [the help channel](https://t.me/alemibothelp)

My personal Telegram userbot. This bot can provide, out of the box, some 
math/moderation/meme/textediting commands. The most relevant features come 
with access to a MongoDB, where messages can be stored. With message caching, 
the bot can provide edit history and show deleted messages.

This project started using Telethon but I migrated to Pyrogram. You can find a `telethon` branch, 
but it won't receive any more support. All features work and it's pretty polished, but the pyro branch 
will receive much more work on.

## Features
* get deleted messages, show edit history
* run python and bash cmds, get info about tg entities
* search on urbandict, english dict, wikipedia
* make figlet, make text slowly appear, make random choices 
* plot, solve and convert text to fancy LaTeX expressions
* deepfry or ascii-art a meme. steal and whip out memes on demand  
* flood with messages, delete messages from users
* upload and download files from hosting server 
* purge messages from specific users

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
The default config contains the usable fields already. You just need to fill in `api_id` and `api_hash`.
You can add a section `[database]` with `username` and `password` for your MongoBD (if you run one). 
By default, modules `crawler`, `inline` and `logger` will be excluded. You can remove them from the `exclude` 
block to enable them again. Be warned that `crawler` will make your account super fishy, `logger` requires 
a MongoDB to connect to and `inline` won't work with users, requires a bot with `inline mode`.

# Dependancies
### Core
* `pyrogram`
* `requests`
### Non-Essential
* `termcolor` : for colored terminal printing. Only in `logger` module.
* `wikipedia`, `italian-dictionary`, `PyDictionary` : used for dictionary searching. Only in `search` module.
* `geopy`, : used for location lookup. Only in `search` module.
* `pyfiglet` : for figlet art, only in `text`
* `pillow` : for frying memes. Only in `memes`
* `sympy` : for math solving and representing. Needs also `matplotlib` for plotting. Only in `math`.
* `pymongo` : for database access. Only in `logger`
* `qrcode` : for making qrcodes. Only in `util`
* `gtts`, `pydub` : for making voice messages. Only in `util`
### Extra
* A `LaTeX` install for making nice math expressions (only in `math`)
* `MongoDB` for storing message data and accessing it (only in `logging`)
* `fortune` for .fortune (only in `text`)
* `ffmpeg` for .voice. `ffmpeg` is tiny but super useful.
* `git` : if you are on Windows, you'll need to install this! It's preinstalled on most Linux distros
