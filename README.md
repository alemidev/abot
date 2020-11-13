# alemibot / ᚨᛚᛖᛗᛁᛒᛟᛏ  v0.1
## Join the bot telegram group on https://t.me/alemibothelp

My personal Telegram userbot. This is still quite early in development but I plan to keep polishing it.
Below some of the available commands right now (the ones with * are restricted to you, others are public)
* `.wiki <something> ` search something on wikipedia
* `.dic <something> ` look up something on english dictionary
* `.ud <something> ` look up something on urban dictionary
* `.roll d<n> ` roll a virtual dice with n faces
* `.fortune ` runs the fortune command on your server (`sudo apt install fortune`)
* `.delme ` delete sent message immediately *
* `.spam [number] <message> ` self explainatory *
* `.purge [target] [number] ` delete last (number) messages from target *
* `.censor [target] ` immediately delete all messages from target in this chat *
* `.run <command> ` execute command on server *

# How to deploy
You just need Python 3.7+ and a PC always on to run this
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
	"cooldown" : 3
}
```
