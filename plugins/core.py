import asyncio
import time
import logging
import io
import re
import json
from datetime import datetime

from bot import alemiBot

from pyrogram import filters

from util.decorators import report_error, set_offline
from util.permission import is_allowed, is_superuser
from util.command import filterCommand
from util.message import edit_or_reply, is_me
from util.user import get_username
from util.help import HelpCategory, HelpEntry, CATEGORIES, ALIASES, get_all_short_text
from util.text import cleartermcolor

logger = logging.getLogger(__name__)

HELP = HelpCategory("CORE")

HELP.add_help(["help"], "get help on cmd or list all cmds", "", args="[cmd]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["help", "h"], list(alemiBot.prefixes)))
@set_offline
async def help_cmd(client, message):
	logger.info("Help!")
	pref = alemiBot.prefixes[0]
	if "cmd" in message.command:
		arg = message.command["cmd"][0]
		for k in CATEGORIES:
			cat = CATEGORIES[k]
			if arg in cat.HELP_ENTRIES:
				e = cat.HELP_ENTRIES[arg]
				return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown")
			elif arg in ALIASES and ALIASES[arg] in cat.HELP_ENTRIES:
				e = cat.HELP_ENTRIES[ALIASES[arg]]
				return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown")
		return await edit_or_reply(message, f"`[!] → ` No command named `{arg}`")
	await edit_or_reply(message, f"`ᚨᛚᛖᛗᛁᛒᛟᛏ v{client.app_version}`\n" +
						get_all_short_text(pref) +
						f"__Commands with * are available to trusted users__", parse_mode="markdown")

HELP.add_help(["asd", "ping"], "a sunny day!",
				"The ping command.", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["asd", "ping"], list(alemiBot.prefixes)))
@set_offline
async def ping(client, message):
	logger.info("Pong")
	before = time.time()
	msg = await edit_or_reply(message, "` → ` a sunny day")
	after = time.time()
	latency = (after - before) * 1000
	await msg.edit(f"` → ` a sunny day `({latency:.0f}ms)`")

HELP.add_help("update", "update and restart",
				"will pull changes from git (`git pull`), install requirements (`pip install -r requirements.txt --upgrade`) " +
				"and then restart process with an `execv` call. If nothing gets pulled from `git`, update will stop unless " +
				"the `-force` flag was given.", args="[-force]")
@alemiBot.on_message(is_superuser & filterCommand("update", list(alemiBot.prefixes), flags=["-force", "-sub"]))
async def update(client, message):
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested update"
	msg = message if is_me(message) else await message.reply(out)
	try:
		logger.info(f"Updating bot ...")
		uptime = str(datetime.now() - client.start_time)
		out += f"\n`→ ` --runtime-- `{uptime}`"
		await msg.edit(out) 
		out += "\n` → ` Fetching updates"
		await msg.edit(out)
		proc = await asyncio.create_subprocess_exec(
			"git", "pull",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT)
		stdout, _stderr = await proc.communicate()
		sub_proc = await asyncio.create_subprocess_exec(
			"git", "submodule", "update", "--remote",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT)
		sub_stdout, _sub_stderr = await sub_proc.communicate()
		sub_count = sub_stdout.count(b"checked out")
		if b"Aborting" in stdout:
			out += " [`FAIL`]\n"
			if "-force" not in message.command["flags"]:
				return await msg.edit(out)
		elif b"Already up to date" in stdout:
			out += " [`N/A`]\n"
			if sub_count < 1 and "-force" not in message.command["flags"]:
				return await msg.edit(out)
		else:
			out += " [`OK`]\n"
		if sub_count > 0:
			out += f"`  → ` Submodule{'s' if sub_count > 1 else ''} [`{sub_count}`]\n"
		out += "` → ` Checking libraries"
		await msg.edit(out) 
		proc = await asyncio.create_subprocess_exec(
			"pip", "install", "-r", "requirements.txt", "--upgrade",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT)
		stdout, _stderr = await proc.communicate()
		if b"ERROR" in stdout:
			out += " [`WARN`]"
		else:
			out += f" [`{stdout.count(b'Collecting')} new`]"
		out += "\n` → ` Restarting process"
		await msg.edit(out) 
		with open("data/lastmsg.json", "w") as f:
			json.dump({"message_id": msg.message_id,
						"chat_id": msg.chat.id}, f)
		asyncio.get_event_loop().create_task(client.restart())
	except Exception as e:
		logger.exception("Error while updating")
		out += " [FAIL]\n`[!] → ` " + str(e)
		await msg.edit(out) 

HELP.add_help(["install", "plugin_add"], "install a plugin",
			  "install a plugin. alemiBot plugins are git repos, cloned " +
			  "into the `plugins` folder as git submodules. You can specify which extension to " +
			  "install by giving `user/repo`. For example, `alemigliardi/statistics`. You can specify " +
			  "which branch to clone with `-b` option. You can also specify a custom folder to clone into with `-d` option.",
			  args="[-b branch] [-d directory] <link-repo>")
@alemiBot.on_message(is_superuser & filterCommand(["install", "plugin_add"], list(alemiBot.prefixes), options={
	"dir": ["-d"],
	"branch": ["-b"]
}))
@report_error(logger)
@set_offline
async def plugin_add(client, message):
	if "cmd" not in message.command:
		return await edit_or_reply(message, "`[!] → ` No input")
	plugin = message.command["cmd"][0]
	branch = message.command["branch"] if "branch" in message.command else "main"
	folder = message.command["dir"] if "dir" in message.command else plugin.split("/")[1]
	link = f"git@github.com:{plugin}.git"

	msg = await edit_or_reply(message, f"` → ` Adding plugin `{plugin}`")

	output = message.text + f"\n` → ` Adding plugin `{plugin}`"

	logger.info(f"Adding plugin \"{plugin}\"")
	proc = await asyncio.create_subprocess_shell(
	  f"git submodule add -b {branch} {link} plugins/{folder}",
	  stdout=asyncio.subprocess.PIPE,
	  stderr=asyncio.subprocess.STDOUT)

	stdout, _sterr = await proc.communicate()
	res = cleartermcolor(stdout.decode())
	if "ERROR: Repository not found" in res:
		await msg.edit(output + f"\n`[!] → ` No plugin `{plugin}` could be found")
	else:
		await msg.edit(output + "` → ` Installed correctly")

HELP.add_help(["uninstall", "plugin_remove"], "uninstall a plugin",
				"remove an installed plugin. alemiBot plugins are git repos, cloned " +
			  "into the `plugins` folder as git submodulesThis will call `git submodule deinit -f`, " +
				"then remove the related folder in `.git/modules` and last remove " +
				"plugin folder and all its content.", args="<plugin>")
@alemiBot.on_message(is_superuser & filterCommand(["uninstall", "plugin_remove"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def plugin_remove(client, message):
	if "cmd" not in message.command:
		return await edit_or_reply(message, "`[!] → ` No input")
	plugin = message.command["cmd"][0]
	if "/" in plugin: # If user passes <user>/<repo> here too, get just repo name
		plugin = plugin.split("/")[1]
	
	logger.info(f"Removing plugin \"{plugin}\"")
	proc = await asyncio.create_subprocess_shell(
	  f"git submodule deinit -f {plugin} && rm -rf .git/modules/{plugin} && git rm -f plugins/{plugin}",
	  stdout=asyncio.subprocess.PIPE,
	  stderr=asyncio.subprocess.STDOUT)

	stdout, _stderr = await proc.communicate()
	logger.warn(stdout.decode())
	# TODO check stdout for errors!
	await edit_or_reply(message, f"` → ` {plugin} removed")

HELP.add_help(["plugins", "plugin", "plugin_list"], "list all the installed plugin",
				"list installed plugins. Will basically read the `.gitmodules` file")
@alemiBot.on_message(is_superuser & filterCommand(["plugins", "plugin", "plugin_list"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def plugin_list(client, message):
	with open(".gitmodules") as f:
		modules = f.read()

	matches = re.findall(r"url = git@github.com:(?P<p>.*).git", modules)

	text = ""
	for match in matches:
		text += f"` → ` `{match}`\n"

	if len(text) > 0:
		await edit_or_reply(message, text)
	else:
		await edit_or_reply(message, "`[!] → ` No plugins installed")