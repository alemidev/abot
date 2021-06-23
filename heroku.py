#!/usr/bin/env python
"""
This script will deploy and run alemiBot on Heroku.
It will first clone the main repo and move inside, then setup any preloaded plugin.
It will require a session string to work, since you cannot interact with terminal on heroku.
"""
import re
import os
import sys
import signal
import subprocess
import logging

from configparser import ConfigParser


PLUGIN_HTTPS = re.compile(r"http(?:s|):\/\/(?:.*)\/(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")
PLUGIN_SSH = re.compile(r"git@(?:.*)\.(?:.*):(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")
def split_url(url):
	"""get author/plugin from a repo url"""
	match = PLUGIN_HTTPS.match(url)
	if match:
		return match["plugin"], match["author"]
	match = PLUGIN_SSH.match(url)
	if match:
		return match["plugin"], match["author"]
	author, plugin = url.split("/", 1)
	return plugin, author

def install_plugin(user_input):
	"""try to install a plugin as submodule from either an url or author/repo:branch"""
	try:
		force_branch = None
		plugin, author = split_url(user_input) # clear url or stuff around
		if ":" in plugin:
			plugin, force_branch = plugin.split(":", 1)
		logger.info("Installing \"%s/%s\"", author, plugin)
		folder = plugin

		custom_env = os.environ.copy()
		custom_env["GIT_TERMINAL_PROMPT"] = "0"

		if user_input.startswith("http") or user_input.startswith("git@"):
			link = user_input
		else:
			link = f"https://github.com/{author}/{plugin}.git"

		logger.info("Checking branches")
		proc = subprocess.Popen(
		      ["git", "ls-remote", link],
		      stdout=subprocess.PIPE,
		      stderr=subprocess.STDOUT,
			  env=custom_env)
		stdout, _sterr = proc.communicate()
		res = stdout.decode()
		logger.info(res)
		if res.startswith(("ERROR", "fatal", "remote: Not Found")):
			logger.error("Could not find %s", link)
			return
		branch = re.search(r"(?:.*)\tHEAD\n(?:.*)\trefs/heads/(?P<branch>.*)\n", res)["branch"]

		if force_branch:
			branch = force_branch

		logger.info("Fetching source code")

		proc = subprocess.Popen( # Can't add as submodules on heroku since it's not a git repo!
		  ["git", "submodule", "add", "-b", branch, link, f"plugins/{folder}"],
		  stdout=subprocess.PIPE,
		  stderr=subprocess.STDOUT,
		  env=custom_env)

		stdout, _sterr = proc.communicate()
		res = stdout.decode()
		logger.info(res)
		if not res.startswith("Cloning"):
			logger.error("Plugin %s/%s was wrongly uninstalled", author, plugin)
			return
		if "ERROR: Repository not found" in res:
			logger.error("No plugin %s/%s could be found", author, plugin)
			return
		if re.search(r"fatal: '(.*)' is not a commit", res):
			logger.error("Non existing branch %s for plugin %s/%s", branch, author, plugin)
			return
		logger.info("Checking dependancies")
		if os.path.isfile(f"plugins/{plugin}/requirements.txt"):
			proc = subprocess.Popen(
				["pip", "install", "-r", f"plugins/{plugin}/requirements.txt", "--upgrade"],
				stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT)
			stdout, _stderr = proc.communicate()
			logger.info(stdout.decode())
	except Exception:
		logger.exception("Error while installing plugin")
		return

if __name__ == "__main__":
	# setup logging early on
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create formatter and add it to the handlers
	print_formatter = logging.Formatter("> %(message)s")
	ch.setFormatter(print_formatter)
	# add the handlers to the logger
	logger.addHandler(ch)

	env = os.environ.copy()
	env["GIT_TERMINAL_PROMPT"] = "0"
	
	logger.info("Cloning main repo")
	proc = subprocess.Popen(
			["git", "clone", "https://github.com/alemidev/alemibot"],
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
	)
	stdout, _sterr = proc.communicate()
	logger.info(stdout.decode())

	os.chdir("alemibot")

	logger.info("Installing dependancies")
	proc = subprocess.Popen(
			["pip", "install", "-r", "requirements.txt"],
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT
	)
	stdout, _sterr = proc.communicate()
	logger.info(stdout.decode())

	logger.info("Preparing config file")
	cfg = ConfigParser()
	cfg.add_section("pyrogram")
	cfg.set("pyrogram", "api_id", os.environ["API_ID"])
	cfg.set("pyrogram", "api_hash", os.environ["API_HASH"])
	cfg.add_section("plugins")
	cfg.set("plugins", "root", "plugins")
	cfg.add_section("perms")
	cfg.set("perms", "sudo", os.environ.get("SUPERUSERS") or "0")
	cfg.set("perms", "public", os.environ.get("ALLOW_EVERYONE") or "False")
	cfg.set("perms", "allowPlugins", os.environ.get("ALLOW_PLUGINS") or "True")
	cfg.add_section("customization")
	cfg.set("customization", "prefixes", os.environ.get("COMMAND_PREFIXES") or "./!")
	cfg.set("customization", "useSsh", "False")

	with open("config.ini", "w") as f:
		cfg.write(f)

	if os.environ.get("EXTRA_CONFIG"):
		with open("config.ini", "a") as f:
			f.write('\n' + os.environ.get("EXTRA_CONFIG"))

	logger.info("Installing preloaded plugins")

	if os.environ.get("PLUGINS"):
		for p in os.environ["PLUGINS"].split(","):
			install_plugin(p.strip())

	logger.info("Starting bot subprocess")

	proc = subprocess.Popen(
			[sys.executable, os.getcwd() + '/bot.py', os.environ["SESSION_STRING"]],
			stdout=sys.stdout, stderr=sys.stderr
	)

	def stop_bot(signum, frame):
		"""will sigint bot subprocess"""
		logger.info("Received SIGTERM, stopping bot subprocess")
		os.kill(proc.pid, signal.SIGINT)

	signal.signal(signal.SIGTERM, stop_bot)

	proc.wait()
	
	logger.info("Worker exiting")