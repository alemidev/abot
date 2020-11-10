# alemibot
My Telegram userbot

# How to use
* You need python3
* `git clone` this repo
* Make a `venv` with `python3 -m venv <anyfolder>`
* Activate `venv` with `source <venvfolder>/bin/activate`
* Install required libraries with `pip install -r requirements.txt`
* Make a file `config.json` with your API hash and ID (visit https://my.telegram.org/)
* Run bot : `./bot.py` or `python bot.py`

## config file
You need to make a config file with this format and drop it next to the bot file :
```json
{
	"NAME" : "alemibot", // or anything else really
	"ID" : <api-id , it's an integer> ,
	"HASH" : "<api-hash, it's a string>"
}```
