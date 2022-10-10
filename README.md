# alemibot
**My Telegram bot/userbot framework**

This repo contains the root for alemibot:
* `core` plugin
* utils
* config file
* folders

### Features
* a centralized config file
* a command parsing system (UNIX-like) to implement sophisticated commands
* an help command which automatically extracts docstrings
* a 2 role permission system (user/root)
* a wrapper around pyrogram SQLite db, for easy storage of persistent data
* some common commands (/update, /ping, /info)
* events for bot startup/shutdown
* some utility functions to handle most common tasks
* a plugin manager (with git submodules), allowing plugins to access all above features

alemiBot simplifies my bot development, by providing a standardized and solid baseline, with common features to all projects, which can focus on their specific functionalities.

# Some plugins
* `alemidev/alemibot-debugtool` very useful tools for debugging and interacting with server
* `alemidev/alemibot-tricks` my biggest collection of "trick command": fancy stuff to show off
* `alemidev/alemibot-moderation` a powerful purge command, to precisely delete messages, plus a small censor utility
* ... more to come, send me your plugins!

## Making custom plugins
To develop your own plugins for alemiBot, you should clone first this repository and work in a folder in the `plugins` directory.
Each plugin must be a repository itself which can be installed in the `plugins` folder as a submodule.

**One "catch":** your plugin should import its files as `import plugins.<yourplugin>.<...>`. This means that if you need to have custom classes, you cannot have dashes (`-`) in your plugin name. Thinking about solutions... On the flip side, you can always access utils

# How to deploy
You just need Python 3.7+ and a PC always on to run this. More dependancies will depend on modules.
It is strongly recommended to install this on a UNIX system. If you plan to install on Windows, [I recommend installing alemibot inside a WSL](https://docs.microsoft.com/en-us/windows/wsl/install-win10)
* Clone this repo : `git clone https://github.com/alemidev/alemibot.git`
* Make a `venv` with `python3 -m venv <anyfolder>`
* Activate `venv` with `source <venvfolder>/bin/activate`
* Install the `alemibot` package in your new venv: `pip install ./alemibot`
* Copy `default.ini` to another file (`my-bot.ini`, for example, use any name) and fill in your API hash and ID (visit https://my.telegram.org/)
* Run bot : `python -m alemibot my-bot`, pass your config name as argument. First time it will request your phone number and a verification code.

# config file
Only required fields are `api_id` and `api_hash`. There is an example config file (`default.ini`) where you just need to fill `api_id` and `api_hash`.
Multiple bot instances can be run with just 1 installation: just give unique names to your configurations and run the correct one: `python -m alemibot <config-name>`.

```ini
[pyrogram]
api_id = 1234                     # your API ID
api_hash = longstring             # your API hash
[perms]
sudo = 0                          # users allowed to operate this account as sudo. Put ids, separate with whitespace
public = False                    # commands for allowed users will be available to everyone
allowPlugins = True               # allow superusers to install more plugins
[customization]
prefixes = .!                     # bot prefixes
useSsh = False                    # use ssh to clone more plugins
desc = A bot made with alemibot   # description to display in /help
[plugins]
root = plugins                    # change plugins folder, leave this as is
```

Plugins may add categories or fields to the config file, refer to their instructions for further configuration.

# Contacts
### Join [the help channel](https://t.me/alemibothelp)
or mail `me@alemi.dev`
