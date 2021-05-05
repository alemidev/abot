import asyncio
import time
import logging
import io
import os
import re
import json
from datetime import datetime

from bot import alemiBot

from pyrogram import filters
from pyrogram.errors import PeerIdInvalid

from util.decorators import report_error, set_offline
from util.permission import is_allowed, is_superuser, allow, disallow, list_allowed, check_superuser
from util.command import filterCommand
from util.message import edit_or_reply, is_me
from util.getters import get_username
from util.text import cleartermcolor
from util.help import HelpCategory, CATEGORIES, ALIASES, get_all_short_text

logger = logging.getLogger(__name__)

HELP = HelpCategory("CORE")

HELP.add_help(["help"], "get help on cmd or list all cmds", "", args="[cmd]", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["help", "h"], list(alemiBot.prefixes)))
@report_error(logger)
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
			# elif arg.lower() == k.lower():
				# TODO print all commands in a category
		return await edit_or_reply(message, f"`[!] → ` No command named `{arg}`")
	await edit_or_reply(message, f"`ᚨᛚᛖᛗᛁᛒᛟᛏ v{client.app_version}`\n" +
						get_all_short_text(pref, sudo=check_superuser(message)),
						parse_mode="markdown",
						disable_web_page_preview=True)

HELP.add_help(["asd", "ping"], "a sunny day!",
				"The ping command.", public=True)
@alemiBot.on_message(is_allowed & filterCommand(["asd", "ping"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def ping_cmd(client, message):
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
async def update_cmd(client, message):
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested update"
	msg = message if is_me(message) else await message.reply(out)
	uptime = str(datetime.now() - client.start_time)
	out += f"\n`→ ` --runtime-- `{uptime}`"
	try:
		logger.info(f"Updating bot ...")
		out += "\n` → ` Fetching updates"
		pulled = False
		await msg.edit(out)
		proc = await asyncio.create_subprocess_exec(
			"git", "pull",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT)
		stdout, _stderr = await proc.communicate()
		logger.info(stdout.decode())
		if b"Aborting" in stdout:
			out += " [`FAIL`]\n"
			if "-force" not in message.command["flags"]:
				return await msg.edit(out)
		elif b"Already up to date" in stdout:
			out += " [`N/A`]"
		else:
			pulled = True
			out += " [`OK`]"

		if os.path.isfile(".gitmodules"): # Also update plugins
			out += "\n`  → ` Submodules"
			await msg.edit(out)
			sub_proc = await asyncio.create_subprocess_exec(
				"git", "submodule", "update", "--remote",
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.STDOUT)
			sub_stdout, _sub_stderr = await sub_proc.communicate()
			logger.info(sub_stdout.decode())
			sub_count = sub_stdout.count(b"checked out")
			if sub_count > 0:
				out += f" [`{sub_count}`]"
				pulled = True
			else:
				out += " [`N/A`]"

		if not pulled and "-force" not in message.command["flags"]:
			return await msg.edit(out)

		out += "\n` → ` Checking libraries"
		await msg.edit(out) 
		proc = await asyncio.create_subprocess_exec(
			"pip", "install", "-r", "requirements.txt", "--upgrade",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT)
		stdout, _stderr = await proc.communicate()
		logger.info(stdout.decode())
		if b"ERROR" in stdout:
			out += " [`WARN`]"
		else:
			out += f" [`{stdout.count(b'Collecting')} new`]"
		if os.path.isfile(".gitmodules"): # Also install dependancies from plugins
			out += "\n`  → ` Submodules"
			await msg.edit(out)
			with open(".gitmodules") as f:
				modules = f.read()
			matches = re.findall(r"path = (?P<path>plugins/[^ ]+)\n", modules)
			count = 0
			for match in matches:
				if os.path.isfile(f"{match}/requirements.txt"):
					proc = await asyncio.create_subprocess_exec(
						"pip", "install", "-r", f"{match}/requirements.txt", "--upgrade",
						stdout=asyncio.subprocess.PIPE,
						stderr=asyncio.subprocess.STDOUT)
					stdout, _stderr = await proc.communicate()
					logger.info(stdout.decode())
					if b"ERROR" in stdout:
						out += " [`WARN`]"
					else:
						count += stdout.count(b'Collecting')
			out += f" [`{count} new`]"
		out += "\n` → ` Restarting process"
		await msg.edit(out) 
		with open("data/lastmsg.json", "w") as f:
			json.dump({"message_id": msg.message_id,
						"chat_id": msg.chat.id}, f)
		asyncio.get_event_loop().create_task(client.restart())
	except Exception as e:
		logger.exception("Error while updating")
		out += " [`FAIL`]\n`[!] → ` " + str(e)
		await msg.edit(out) 

PLUGIN_HTTPS = re.compile(r"https://(?:.*)\.(?:.*)/(?P<plugin>[^ ]+)\.git")
PLUGIN_SSH = re.compile(r"git@(?:.*)\.(?:.*):(?P<plugin>[^ ]+)\.git")
def get_plugin(url):
	match = PLUGIN_HTTPS.match(url)
	if match:
		return match["plugin"]
	match = PLUGIN_SSH.match(url)
	if match:
		return match["plugin"]
	return url

HELP.add_help(["install", "plugin_add"], "install a plugin",
				"install a plugin. alemiBot plugins are git repos, cloned into the `plugins` folder as git submodules. " +
				"You can specify which extension to install by giving `user/repo` (will default to github.com), " +
				"or specify the entire url. For example, `alemigliardi/statistics` is the same as " +
				"`git@github.com:alemigliardi/statistics.git`. You can specify " +
				"which branch to clone with `-b` option. You can also specify a custom folder to clone into with `-d` option.",
				args="[-b branch] [-d directory] <link-repo>")
@alemiBot.on_message(is_superuser & filterCommand(["install", "plugin_add"], list(alemiBot.prefixes), options={
	"dir": ["-d"],
	"branch": ["-b"]
}))
async def plugin_add_cmd(client, message):
	if not alemiBot.allow_plugin_install:
		return await edit_or_reply(message, "`[!] → ` Plugin management is disabled")
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested plugin install"
	msg = message if is_me(message) else await message.reply(out)
	try:
		if "cmd" not in message.command:
			out += "\n`[!] → ` No input"
			return await msg.edit(out)
		user_input = message.command["cmd"][0]
		branch = message.command["branch"] if "branch" in message.command else None
		folder = message.command["dir"] if "dir" in message.command else None
		if user_input.startswith("http") or user_input.startswith("git@"):
			link = user_input
		else: # default to github over ssh
			link = f"git@github.com:{user_input}.git"

		plugin_author = get_plugin(user_input) # clear url or stuff around
		author, plugin = plugin_author.split("/", 1)
		if folder is None:
			folder = plugin

		out += f"\n`→ ` Installing `{author}/{plugin}`"
		logger.info(f"Installing \"{author}/{plugin}\"")

		if os.path.isfile(".gitmodules"):
			with open(".gitmodules") as f:
				modules = f.read()
			matches = re.findall(r"url = git@github.com:(?P<p>.*).git", modules)
			for match in matches:
				if match == plugin:
					out += "`[!] → ` Plugin already installed"
					return await msg.edit(out)

		if branch is None:
			out += "\n` → ` Checking branches"
			await msg.edit(out)
			proc = await asyncio.create_subprocess_shell(
			      f"git ls-remote {link}",
			      stdout=asyncio.subprocess.PIPE,
			      stderr=asyncio.subprocess.STDOUT)
			stdout, _sterr = await proc.communicate()
			res = cleartermcolor(stdout.decode())
			logger.info(res)
			if res.startswith("ERROR"):
				out += f" [`FAIL`]\n`[!] → ` Could not find `{link}`"
				return await msg.edit(out)
			out += " [`OK`]"
			branch = re.search(r"(?:.*)\tHEAD\n(?:.*)\trefs/heads/(?P<branch>.*)\n", res)["branch"]

		out += "\n` → ` Fetching source code"
		await msg.edit(out)

		proc = await asyncio.create_subprocess_shell(
		  f"git submodule add -b {branch} {link} plugins/{folder}",
		  stdout=asyncio.subprocess.PIPE,
		  stderr=asyncio.subprocess.STDOUT)

		stdout, _sterr = await proc.communicate()
		res = cleartermcolor(stdout.decode())
		logger.info(res)
		if not res.startswith("Cloning"):
			out += f" [`FAIL`]\n`[!] → ` Plugin `{author}/{plugin}` was wrongly uninstalled"
			return await msg.edit(out)
		if "ERROR: Repository not found" in res:
			out += f" [`FAIL`]\n`[!] → ` No plugin `{author}/{plugin}` could be found"
			return await msg.edit(out)
		if re.search(r"fatal: '(.*)' is not a commit", res):
			out += f" [`FAIL`]\n`[!] → ` Non existing branch `{branch}` for `{author}/{plugin}`"
			return await msg.edit(out)
		out += f" [`OK`]\n` → ` Checking dependancies"
		await msg.edit(out)
		if os.path.isfile(f"plugins/{plugin}/requirements.txt"):
			proc = await asyncio.create_subprocess_exec(
				"pip", "install", "-r", f"plugins/{plugin}/requirements.txt", "--upgrade",
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.STDOUT)
			stdout, _stderr = await proc.communicate()
			logger.info(stdout.decode())
			if b"ERROR" in stdout:
				logger.warn(stdout.decode())
				out += " [`WARN`]"
			else:
				out += f" [`{stdout.count(b'Uninstalling')} new`]"
		else:
			out += " [`N/A`]"
		out += f"\n` → ` Restarting process"
		await msg.edit(out)
		with open("data/lastmsg.json", "w") as f:
			json.dump({"message_id": msg.message_id,
						"chat_id": msg.chat.id}, f)
		asyncio.get_event_loop().create_task(client.restart())
	except Exception as e:
		logger.exception("Error while installing plugin")
		out += " [`FAIL`]\n`[!] → ` " + str(e)
		await msg.edit(out) 

HELP.add_help(["uninstall", "plugin_remove"], "uninstall a plugin",
				"remove an installed plugin. alemiBot plugins are git repos, cloned " +
				"into the `plugins` folder as git submodulesThis will call `git submodule deinit -f`, " +
				"then remove the related folder in `.git/modules` and last remove " +
				"plugin folder and all its content. If flag `-lib` is added, libraries installed with " +
				"pip will be removed too (may break dependancies of other plugins!)", args="[-lib] <plugin>")
@alemiBot.on_message(is_superuser & filterCommand(["uninstall", "plugin_remove"], list(alemiBot.prefixes), flags=["-lib"]))
async def plugin_remove_cmd(client, message):
	if not alemiBot.allow_plugin_install:
		return await edit_or_reply(message, "`[!] → ` Plugin management is disabled")
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested plugin removal"
	msg = message if is_me(message) else await message.reply(out)

	try:
		if "cmd" not in message.command:
			out += "\n`[!] → ` No input"
			return await msg.edit(out)
		plugin = message.command["cmd"][0]

		out += f"\n`→ ` Uninstalling `{plugin}`"

		if "/" in plugin: # If user passes <user>/<repo> here too, get just repo name
			plugin = plugin.split("/")[1]
	
		logger.info(f"Removing plugin \"{plugin}\"")
		if "-lib" in message.command["flags"]:
			out += "\n` → ` Removing libraries"
			await msg.edit(out)
			if os.path.isfile(f"plugins/{plugin}/requirements.txt"):
				proc = await asyncio.create_subprocess_exec(
					"pip", "uninstall", "-y", "-r", f"plugins/{plugin}/requirements.txt",
					stdout=asyncio.subprocess.PIPE,
					stderr=asyncio.subprocess.STDOUT)
				stdout, _stderr = await proc.communicate()
				logger.info(stdout.decode())
				if b"ERROR" in stdout:
					out += " [`WARN`]"
				else:
					out += f" [`{stdout.count(b'Uninstalling')} del`]"
		out += "\n` → ` Removing source code" 
		await msg.edit(out)
		proc = await asyncio.create_subprocess_shell(
		  f"git submodule deinit -f plugins/{plugin} && rm -rf .git/modules/plugins/{plugin} && git rm -f plugins/{plugin}",
		  stdout=asyncio.subprocess.PIPE,
		  stderr=asyncio.subprocess.STDOUT)

		stdout, _stderr = await proc.communicate()
		res = cleartermcolor(stdout.decode())
		logger.info(res)
		if not res.startswith("Cleared"):
			logger.error(res)
			out += f" [`FAIL`]\n`[!] → ` Could not deinit `{plugin}`"
			return await msg.edit(out)
		if f"rm 'plugins/{plugin}'" not in res:
			logger.error(res)
			out += f" [`FAIL`]\n`[!] → ` Could not delete `{plugin}`"
			return await msg.edit(out)
		out += f" [`OK`]\n` → ` Restarting process"
		await msg.edit(out)
		with open("data/lastmsg.json", "w") as f:
			json.dump({"message_id": msg.message_id,
						"chat_id": msg.chat.id}, f)
		asyncio.get_event_loop().create_task(client.restart())
	except Exception as e:
		logger.exception("Error while installing plugin")
		out += " [`FAIL`]\n`[!] → ` " + str(e)
		await msg.edit(out) 

HELP.add_help(["plugins", "plugin", "plugin_list"], "list all the installed plugin",
				"list installed plugins. Will basically read the `.gitmodules` file")
@alemiBot.on_message(is_superuser & filterCommand(["plugins", "plugin", "plugin_list"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def plugin_list_cmd(client, message):
	hidden = alemiBot.config.get("plugins", "hidden", fallback="").strip().split("\n")
	if os.path.isfile(".gitmodules"):
		with open(".gitmodules") as f:
			modules = f.read()
		matches = re.findall(r"url = git@github.com:(?P<p>.*).git", modules)
		text = "`→ ` Installed plugins:\n"
		for match in matches:
			if match not in hidden:
				text += f"` → ` `{match}`\n"
		await edit_or_reply(message, text)
	else:
		await edit_or_reply(message, "`[!] → ` No plugins installed")

HELP.add_help(["allow", "disallow", "revoke"], "allow/disallow to use bot",
				"this command will work differently if invoked with `allow` or with `disallow`. Target user " +
				"will be given/revoked access to public bot commands. ~~Use `@here` or `@everyone` to allow " +
				"all users in this chat.", args="<target>")
@alemiBot.on_message(is_superuser & filterCommand(["allow", "disallow", "revoke"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def manage_allowed_cmd(client, message):
	users_to_manage = []
	if message.reply_to_message is not None:
		peer = message.reply_to_message.from_user
		if peer is None:
			return
		users_to_manage.append(peer)
	elif "cmd" in message.command:
		if message.command["cmd"][0] in ["@here", "@everyone"]:
			async for u in client.iter_chat_members(message.chat.id):
				if u.user.is_bot:
					continue
				users_to_manage.append(u.user)
		else:
			lookup = [ uname for uname in message.command["cmd"] if uname != "-delme" ]
			try:
				users = await client.get_users(lookup)
				if users is None:
					return await edit_or_reply(message, "`[!] → ` No user matched")
				users_to_manage += users
			except ValueError:
				return await edit_or_reply(message, "`[!] → ` Lookup failed")
	else:
		return await edit_or_reply(message, "`[!] → ` Provide an ID or reply to a msg")
	logger.info("Changing permissions")
	out = ""
	action = allow if message.command["base"] == "allow" else disallow
	action_str = "Allowed" if message.command["base"] == "allow" else "Disallowed"
	for u in users_to_manage:
		if action(u.id, val=get_username(u)):
			out += f"` → ` {action_str} **{get_username(u, mention=True)}**\n"
	if out != "":
		await edit_or_reply(message, out)
	else:
		await edit_or_reply(message, "` → ` No changes")

HELP.add_help(["trusted", "plist", "permlist"], "list allowed users",
				"this will be pretty leaky, don't do it around untrusted people! It will attempt " +
				"to get all trusted users in one batch, but if at least one user is not searchable (no " +
				"username and ubot hasn't interacted with it yet), it will lookup users one by one, and " +
				"append ids not searchable at the end.")
@alemiBot.on_message(is_superuser & filterCommand(["trusted", "plist", "permlist"], list(alemiBot.prefixes)))
@report_error(logger)
@set_offline
async def trusted_list_cmd(client, message):
	text = "`[` "
	issues = ""
	logger.info("Listing allowed users")
	try:
		users = await client.get_users(list_allowed()) # raises PeerIdInvalid exc if even one of the ids has not been interacted with
		for u in users:
			text += get_username(u, mention=True) + ", "
	except PeerIdInvalid:
		for uid in list_allowed():									
			try:
				text += get_username(await client.get_users(uid), mention=True) + ", "
			except PeerIdInvalid:
				issues += f"~~[{uid}]~~ "
	text += "`]`"
	await edit_or_reply(message, f"` → ` Allowed Users :\n{text}\n{issues}") 