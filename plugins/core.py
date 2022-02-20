""" TODO split this shit up!!! """
import asyncio
import time
import logging
import platform
import resource
import os
import re
import json
from datetime import datetime

import psutil

from pyrogram import filters
from pyrogram.errors import PeerIdInvalid
from pyrogram.raw.functions import Ping
from pyrogram.raw.functions.account import GetAuthorizations

from alemibot import alemiBot

from alemibot.util import (
	report_error, set_offline, is_allowed, sudo, filterCommand, edit_or_reply, is_me,
	get_username, cleartermcolor, order_suffix, HelpCategory
)

from alemibot.util.help import CATEGORIES, ALIASES, get_all_short_text
from alemibot.util.command import _Message as Message

logger = logging.getLogger(__name__)

HELP = HelpCategory("CORE")

_BASE_HELP_TEMPLATE = """
<code> → </code> List all available commands: <code>{prefix}help -l</code>
<code> → </code> Read a command documentation: <code>{prefix}help update</code>
<code>  → </code> Angle brackets represent user input:
<code>   → </code> <code>{prefix}count &lt;n&gt;</code> (ex: <code>{prefix}count 5</code>).
<code>  → </code> Square brackets for optional parameters:
<code>   → </code> Flag :  <code>{prefix}update [-force]</code> (ex: <code>{prefix}update -force</code>).
<code>   → </code> Option : <code>{prefix}roll [-n &lt;n&gt;]</code> (ex: <code>{prefix}roll -n 100</code>).
<code>   → </code> Argument :  <code>{prefix}query [&lt;payload&gt;]</code> (ex: <code>{prefix}query "abc"</code>).
"""

@HELP.add(cmd="[<cmd>]", sudo=False)
@alemiBot.on_message(is_allowed & filterCommand(["help"], flags=["-l", "--list"]))
@report_error(logger)
@set_offline
async def help_cmd(client:alemiBot, message:Message):
	"""get help on cmd or list all cmds

	Without args, will print all available commands.
	Add a command (.help update) to get details on a specific command
	"""
	pref = client.prefixes[0]
	if message.command["-l"] or message.command["--list"]:
		return await edit_or_reply(message,
			f"<code>ᚨᛚᛖᛗᛁᛒᛟᛏ</code> v<b>{client.app_version}</b>\n" + 
				get_all_short_text(pref, sudo=sudo(client, message)),
			parse_mode="html"
		)
	elif len(message.command) > 0:
		arg = message.command[0]
		# if arg.upper() in CATEGORIES:
			# TODO print all commands in a category
		for k in CATEGORIES:
			cat = CATEGORIES[k]
			if arg in cat.HELP_ENTRIES:
				e = cat.HELP_ENTRIES[arg]
				return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown", disable_web_page_preview=True)
			elif arg in ALIASES and ALIASES[arg] in cat.HELP_ENTRIES:
				e = cat.HELP_ENTRIES[ALIASES[arg]]
				return await edit_or_reply(message, f"`→ {e.title} {e.args} `\n{e.longtext}", parse_mode="markdown", disable_web_page_preview=True)
		return await edit_or_reply(message, f"<code>[!] → </code> No command named <code>{arg}</code>", parse_mode="html")
	else:
		descr = client.config.get("customization", "desc", fallback="")
		if descr:
			descr = f"<code> → </code> <i>{descr}</i>"
		return await edit_or_reply(message,
			descr + _BASE_HELP_TEMPLATE.format(prefix=pref) +
			f"based on <code>ᚨᛚᛖᛗᛁᛒᛟᛏ</code> v<b>{client.app_version}</b>\n",
			parse_mode="html"
		)

@HELP.add(sudo=False)
@alemiBot.on_message(is_allowed & filterCommand(["asd", "ping"]))
@report_error(logger)
@set_offline
async def ping_cmd(client:alemiBot, message:Message):
	"""a sunny day!

	The ping command
	"""
	before = time.time()
	await client.send(Ping(ping_id=69))
	after = time.time()
	latency = (after - before) * 1000
	answer = "a sunny day" if message.command.base == "asd" else "pong"
	await edit_or_reply(message, f"` → ` {answer} (`{latency:.1f}` ms)")

@HELP.add()
@alemiBot.on_message(sudo & filterCommand(["info", "about", "flex"]))
@report_error(logger)
@set_offline
async def info_cmd(client:alemiBot, message:Message):
	"""info about project and client status

	Will show project version+link, current uptime, session age (for users), latency, plugins count and system+load specs.
	The project version is composed as   v `release` - `commit_hash`   , to identify down to the single commit executing code.
	Hardware specs might not be super accurate, especially on virtualized hosts.
	Process CPU usage is calculated as `CPU_TIME / EXECUTION_TIME`. cpu_time includes both user mode and kernel mode.
	CPU usage is thus an average usage across the entirety of the process execution.
	CPU usage will count both main process and any child (still executing or terminated).
	System total CPU usage instead is calculated as a delta since last call. It is a hardly significant value since it fluctuates a lot.
	RAM total and used is calculated appropriately both for process and for system.
	"""
	before = time.time()
	await client.send(Ping(ping_id=69))
	after = time.time()
	latency = (after - before) * 1000
	self_proc = psutil.Process(os.getpid())
	ram_usage = self_proc.memory_percent()
	ram_load = psutil.virtual_memory().percent
	total_ram = psutil.virtual_memory().total
	# cpu_usage = self_proc.cpu_percent() # getting it like this always returns 0
	# 									  # let's instead calculate CPU usage as cpu_time/execution_time
	execution_time = (datetime.now() - client.start_time).total_seconds()
	res_self = resource.getrusage(resource.RUSAGE_SELF)
	res_child = resource.getrusage(resource.RUSAGE_CHILDREN)
	cpu_time = res_self.ru_utime + res_child.ru_utime + res_self.ru_stime + res_child.ru_stime
	cpu_usage = cpu_time / execution_time
	cpu_load = psutil.cpu_percent() # total
	cpu_count = psutil.cpu_count()
	cpu_freq = max(psutil.cpu_freq().max, psutil.cpu_freq().current) # max might be 0 and current might be lower than max
	with open(".gitmodules") as f: # not too nice but will do for now
		plugin_count = f.read().count("[submodule")
	
	if not client.me.is_bot:
		sess = list(filter(lambda x : x.current , (await client.send(GetAuthorizations())).authorizations))[0]
		session_age = datetime.now() - datetime.utcfromtimestamp(sess.date_created)
	
	await edit_or_reply(message,
		f'<code>→ </code> <a href="https://github.com/alemidev/alemibot">ᚨᛚᛖᛗᛁᛒᛟᛏ</a> <code>v{client.app_version}</code>\n' +
		f"<code> → </code> <b>uptime</b> <code>{str(datetime.now() - client.start_time)}</code>\n" +
		(f"<code>  → </code> <b>session age</b> <code>{str(session_age)}</code>\n" if not client.me.is_bot else "") +
		f"<code> → </code> <b>latency</b> <code>{latency:.1f} ms</code>\n" +
		f"<code> → </code> <b>plugins</b> <code>{plugin_count}</code>\n" +
		f"<code>→ </code> <b>system</b> <code>{platform.system()}-{platform.machine()} {platform.release()}</code>\n" +
		f"<code> → </code> <b>cpu [</b><code>{cpu_count}x {cpu_freq/1000:.1f}GHz</code><b>] load</b> <code>{cpu_usage:.2f}%</code> (<code>{cpu_load:.2f}%</code> system)\n" +
		f"<code> → </code> <b>mem [</b><code>{order_suffix(total_ram)}</code><b>] use</b> <code>{ram_usage:.2f}%</code> (<code>{ram_load:.2f}%</code> system)\n" +
		f"<code>→ </code> <b>python</b> <code>{platform.python_version()}</code>\n",
		parse_mode="html", disable_web_page_preview=True
	)

@HELP.add()
@alemiBot.on_message(sudo & filterCommand("update", flags=["-force"]))
async def update_cmd(client:alemiBot, message:Message):
	"""fetch updates and restart client

	Will pull changes from git (`git pull`), install requirements (`pip install -r requirements.txt --upgrade`) \
	and then restart process with an `execv` call.
	If nothing gets pulled from `git`, update will stop unless the `-force` flag was given.
	"""
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested update"
	msg = message if is_me(message) else await message.reply(out)
	uptime = str(datetime.now() - client.start_time)
	out += f"\n`→ ` --runtime-- `{uptime}`"
	try:
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
			if not message.command["-force"]:
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

		if not pulled and not message.command["-force"]:
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
		if msg.chat:
			client.storage._set_last_message(msg.chat.id, msg.message_id)
		asyncio.get_event_loop().create_task(client.restart())
	except Exception as e:
		logger.exception("Error while updating")
		out += " [`FAIL`]\n`[!] → ` " + str(e)
		await msg.edit(out) 

PLUGIN_HTTPS = re.compile(r"http(?:s|):\/\/(?:.*)\/(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")
PLUGIN_SSH = re.compile(r"git@(?:.*)\.(?:.*):(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")
def split_url(url):
	match = PLUGIN_HTTPS.match(url)
	if match:
		return match["plugin"], match["author"]
	match = PLUGIN_SSH.match(url)
	if match:
		return match["plugin"], match["author"]
	author, plugin = url.split("/", 1)
	return plugin, author

@HELP.add(cmd="<plugin>")
@alemiBot.on_message(sudo & filterCommand(["install", "plugin_add"], options={
	"dir": ["-d", "--dir"],
	"branch": ["-b", "--branch"],
}, flags=["-ssh"]))
async def plugin_add_cmd(client:alemiBot, message:Message):
	"""install a plugin

	alemiBot plugins are git repos, cloned into the `plugins` folder as git submodules.
	You can specify which extension to install by giving `user/repo` (will default to github.com), or specify the entire url.
	For example,
		`alemidev/alemibot-tricks`
	is the same as
		`https://github.com/alemidev/alemibot-tricks.git`
	By default, https will be used (meaning that if you try to clone a private repo, it will just fail).
	You can make it clone using ssh	with `-ssh` flag, or by adding `useSsh = True` to your config (under `[customization]`).
	You can also include your GitHub credentials in the clone url itself:
		`https://username:password@github.com/author/repo.git`
	Your github credentials will be stored in plain text inside project folder. \
	Because of this, it is --not recommended-- to include credentials in the clone url. Set up an ssh key for private plugins.
	You can specify which branch to clone with `-b` option.
	You can also specify a custom folder to clone into with `-d` option (this may break plugins relying on data stored in their directory!)
	"""
	if not client.config.getboolean("perms", "allowPlugins", fallback=True):
		return await edit_or_reply(message, "`[!] → ` Plugin management is disabled")
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested plugin install"
	msg = message if is_me(message) else await message.reply(out)
	try:
		if len(message.command) < 1:
			out += "\n`[!] → ` No input"
			return await msg.edit(out)
		user_input = message.command[0]
		branch = message.command["branch"]
		folder = message.command["dir"]

		plugin, author = split_url(user_input) # clear url or stuff around
		if folder is None:
			folder = plugin

		if user_input.startswith("http") or user_input.startswith("git@"):
			link = user_input
		else:
			if client.config.getboolean("customization", "useSsh", fallback=False) or message.command["-ssh"]:
				link = f"git@github.com:{author}/{plugin}.git"
			else:
				link = f"https://github.com/{author}/{plugin}.git"

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
				f"GIT_TERMINAL_PROMPT=0 git ls-remote --symref {link} HEAD",
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.STDOUT
			)
			stdout, _sterr = await proc.communicate()
			res = cleartermcolor(stdout.decode())
			logger.info(res)
			if res.startswith(("ERROR", "fatal", "remote: Not Found")):
				out += f" [`FAIL`]\n`[!] → ` Could not find `{link}`"
				return await msg.edit(out)
			out += " [`OK`]"
			match = re.search(r"refs\/heads\/(?P<branch>[^\s]+)(?:\s+)HEAD", res)
			branch = match['branch'] if match else 'UNKNOWN'

		out += "\n` → ` Fetching source code"
		await msg.edit(out)

		proc = await asyncio.create_subprocess_shell(
			f"GIT_TERMINAL_PROMPT=0 git submodule add -b {branch} {link} plugins/{folder}",
			stdout=asyncio.subprocess.PIPE,
			stderr=asyncio.subprocess.STDOUT
		)

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

# TODO maybe I can merge these 2 commands like trust/revoke ?

@HELP.add(cmd="<plugin>")
@alemiBot.on_message(sudo & filterCommand(["uninstall", "plugin_remove"], flags=["-lib"]))
async def plugin_remove_cmd(client:alemiBot, message:Message):
	"""remove an installed plugin.

	alemiBot plugins are git repos, cloned into the `plugins` folder as git submodules.
	This will call `git submodule deinit -f`, then remove the related folder in `.git/modules` and last remove \
	plugin folder and all its content.
	If flag `-lib` is added, libraries installed with pip will be removed too (may break dependancies of other plugins!)
	"""
	if not client.config.getboolean("perms", "allowPlugins", fallback=True):
		return await edit_or_reply(message, "`[!] → ` Plugin management is disabled")
	out = message.text.markdown if is_me(message) else f"`→ ` {get_username(message.from_user)} requested plugin removal"
	msg = message if is_me(message) else await message.reply(out)

	try:
		if len(message.command) < 1:
			out += "\n`[!] → ` No input"
			return await msg.edit(out)
		plugin = message.command[0]

		out += f"\n`→ ` Uninstalling `{plugin}`"

		if "/" in plugin: # If user passes <user>/<repo> here too, get just repo name
			plugin = plugin.split("/")[1]
	
		logger.info(f"Removing plugin \"{plugin}\"")
		if message.command["-lib"]:
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

@HELP.add()
@alemiBot.on_message(sudo & filterCommand(["plugins", "plugin", "plugin_list"]))
@report_error(logger)
@set_offline
async def plugin_list_cmd(client:alemiBot, message:Message):
	"""list installed plugins.

	Will basically read the `.gitmodules` file
	"""
	hidden = client.config.get("plugins", "hidden", fallback="").strip().split("\n")
	if os.path.isfile(".gitmodules"):
		with open(".gitmodules") as f:
			modules = f.read()
		matches = re.findall(r"url = (?:git@|https:\/\/(?:www\.|))github\.com(?::|\/)(?P<p>[^ \.]+)(?:\.git|)", modules)
		text = "`→ ` Installed plugins:\n"
		for match in matches:
			if match not in hidden:
				text += f"` → ` `{match}`\n"
		await edit_or_reply(message, text)
	else:
		await edit_or_reply(message, "`[!] → ` No plugins installed")

@HELP.add(cmd="[<target>]")
@alemiBot.on_message(sudo & filterCommand(["allow", "disallow", "revoke"], options={
	'group' : ['-g', '--group'],
}))
@report_error(logger)
@set_offline
async def manage_allowed_cmd(client:alemiBot, message:Message):
	"""allow/disallow target user

	This command will work differently if invoked with `allow` or with `disallow`.
	Target user will be given/revoked access to public bot commands. Use `@here` or `@everyone` to allow \
	all users in current chat.
	"""
	users_to_manage = []
	if message.reply_to_message is not None:
		peer = message.reply_to_message.from_user
		if peer is None:
			return
		users_to_manage.append(peer)
	elif len(message.command) > 0:
		if message.command[0] in ["@here", "@everyone"]:
			async for u in client.iter_chat_members(message.chat.id):
				if u.user.is_bot:
					continue
				users_to_manage.append(u.user)
		else:
			lookup = [ uname for uname in message.command.arg if uname != "-delme" ]
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
	action = client.auth.put if message.command.base == "allow" else client.auth.pop
	action_str = "Allowed" if message.command.base == "allow" else "Disallowed"
	for u in users_to_manage:
		if action(u.id, message.command['group'] or '_'):
			out += f"` → ` {action_str} **{get_username(u, mention=True)}**\n"
	if out != "":
		await edit_or_reply(message, out)
	else:
		await edit_or_reply(message, "` → ` No changes")

@HELP.add()
@alemiBot.on_message(sudo & filterCommand(["trusted", "plist", "permlist"]))
@report_error(logger)
@set_offline
async def trusted_list_cmd(client:alemiBot, message:Message):
	"""list allowed users

	This will be pretty leaky, don't do it around untrusted people!
	It will attempt to get all trusted users in one batch. If at least one user is not \
	searchable (no username and ubot hasn't interacted with it yet), it will lookup users \
	one by one and append non searchable ids at the end.
	"""
	text = "`[` "
	issues = ""
	try:
		users = await client.get_users(client.auth.all()) # raises PeerIdInvalid exc if even one of the ids has not been interacted with
		for u in users:
			text += get_username(u, mention=True) + ", "
	except PeerIdInvalid:
		for uid in client.auth.all():
			try:
				text += get_username(await client.get_users(uid), mention=True) + ", "
			except PeerIdInvalid:
				issues += f"~~[{uid}]~~ "
	text += "`]`"
	await edit_or_reply(message, f"` → ` Allowed Users :\n{text}\n{issues}") 
