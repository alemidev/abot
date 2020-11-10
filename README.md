# alemibot / ᚨᛚᛖᛗᛁᛒᛟᛏ  v0.1
My personal Telegram userbot. This is kinda early but I plan to work a little on this.
Below some available commands right now (the ones with * are restricted)
* `.help ` print help message
* `.wiki <something> ` search something on wikipedia
* `.diz <something> ` look up something on italian dictionary
* `.shrug ` replace or reply with shrug composite emote
* `.roll d<n> ` roll a virtual dice with n faces
* `.fortune ` you feel lucky!?
* `.delete ` delete sent message immediately *
* `.spam <number> <message> ` self explainatory *
* `.run <command> ` execute command on server *
* `.save ` save attached file to server *
* `.upload ` upload a file from server to chat *

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
	"HASH" : "l00k4tm31m4nh45h"
}
```
