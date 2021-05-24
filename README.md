# alemibot
**My Telegram bot/userbot framework##**

This repo contains the root for alemibot:
* `core` plugin
* utils
* config file
* folders

alemiBot comes with a 2 role permission system builtin, an easy to implement help command and a plugin manager. It also bundles many utils I use across plugins.

alemiBot simplifies my bot development, by providing a standardized and solid baseline, with common features to all projects, which can focus on their specific functionalities.

# Some plugins
* `alemidev/alemibot-debugtool` very useful tools for debugging and interacting with server
* `alemidev/alemibot-tricks` my biggest collection of "trick command": fancy stuff to show off
* ... more to come, send me your plugins!

# Making plugins
To develop your own plugins for alemiBot, you should clone first this repository and work in a folder in the `plugins` directory.
Each plugin must be a repository itself which can be installed in the `plugins` folder as a submodule.
### One "catch"
Your plugin should import its files as `import plugins.<yourplugin>.<...>`. This means that if you need to have custom classes, you cannot have dashes (`-`) in your plugin name. Thinking about solutions... On the flip side, you can always access utils

# How to deploy
You just need Python 3.7+ and a PC always on to run this. More dependancies will depend on modules.
It is strongly recommended to install this on a UNIX system. If you plan to install on Windows, 
[I recommend installing alemibot inside a WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* Clone this repo : `git clone https://github.com/alemidev/alemibot.git`
* Make a `venv` with `python3 -m venv <anyfolder>`
* Activate `venv` with `source <venvfolder>/bin/activate`
* Install required libraries with `pip install -r requirements.txt`
* Edit the `config.ini` file with your API hash and ID (visit https://my.telegram.org/)
* Run bot : `python bot.py`. First time it will request your phone number and a verification code.

## config file
Only required fields are `api_id` and `api_hash`. There is an example config file (`config.ini.example`) where you just need to fill `api_id` and `api_hash`. (remember to rename it in just `config.ini`!)

```ini
[pyrogram]
api_id = 1234 # your API ID
api_hash = longstring # your API hash
[perms]
sudo = 0 # users allowed to operate this account as sudo. Put ids, separate with whitespace
public = False # commands for allowed users will be available to everyone
allowPlugins = True # allow superusers to install more plugins
[customization]
prefixes = .! # bot prefixes
useSsh = False # use ssh to clone more plugins
[plugins]
root = plugins # change plugins folder, leave this as is
[database] # unused by default but common in plugins!
```

Plugins may add categories or fields to the config file.

# Contacts
### Join [the help channel](https://t.me/alemibothelp)
or mail `me@alemi.dev`
