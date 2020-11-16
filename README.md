# alemibot / ᚨᛚᛖᛗᛁᛒᛟᛏ  v0.1
### Join the bot telegram group on https://t.me/alemibothelp

My personal Telegram userbot. This bot can provide, out of the box, some 
math/moderation/meme/textediting commands. The most relevant features come 
with access to a MongoDB, where messages can be stored. With message caching, 
the bot can provide edit history and show deleted messages.

Right now modules are added inside `bot.py`. You can comment out and add any. 
A more proper module loader will be done eventually to allow easier module configuration.

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
* `git clone` this repo
* Make a `venv` with `python3 -m venv <anyfolder>`
* Activate `venv` with `source <venvfolder>/bin/activate`
* Install required libraries with `pip install -r requirements.txt`
* Make a file `config.json` with your API hash and ID (visit https://my.telegram.org/)
* Run bot : `./bot.py` or `python bot.py`

## config file
You need to make a config file similar to this and drop it next to the bot file :
```json
{
	"NAME" : "alemibot",
	"ID" : 1234,
	"HASH" : "l00k4tm31m4nh45h",
	"cooldown" : 3,
	"USER_DB" : "username",
	"PASS_DB" : "password"
}
```
Ye, pwd in plaintext, ugh. I plan to make `pass` integrateable with it

# Dependancies
### Core
* `telethon`
* `requests`
### Non-Essential
* `termcolor` : for colored terminal printing. Only in `logger` module.
* `wikipedia`, `italian-dictionary`, `PyDictionary` : used for dictionary searching. Only in `search` module.
* `pyfiglet` : for figlet art, only in `text`
* `pillow` : for frying memes. Only in `memes`
* `sympy` : for math solving and representing. Needs also `matplotlib` for plotting. Only in `math`.
* `pymongo` : for database access. Only in `logger`
### Extra
* A `LaTeX` install for making nice math expressions (only in `math`)
* `MongoDB` for storing message data and accessing it (only in `logging`)
* `fortune` for .fortune (only in `text`)
