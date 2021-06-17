#!/usr/bin/env python
"""
"""
import re
import os
import subprocess
import logging

from configparser import ConfigParser

logger = logging.getLogger("SETUP")

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

def install_plugin(user_input):
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
	except Exception as e:
		logger.exception("Error while installing plugin")
		return

if __name__ == "__main__":
	env = os.environ.copy()
	env["GIT_TERMINAL_PROMPT"] = "0"
	
	proc = subprocess.Popen(
			["git", "clone", "https://github.com/alemidev/alemibot"],
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
	)

	os.chdir(os.getcwd() + "/alemibot")

	cfg = ConfigParser()
	cfg["pyrogram"]["api_id"] = os.environ["API_ID"]
	cfg["pyrogram"]["api_hash"] = os.environ["API_HASH"]
	cfg["plugins"]["root"] = "plugins"
	cfg["perms"]["sudo"] = os.environ.get("SUPERUSERS") or 0
	cfg["perms"]["public"] = bool(os.environ.get("ALLOW_EVERYONE"))
	cfg["perms"]["allowPlugins"] = os.environ.get("ALLOW_PLUGINS") or True
	cfg["customization"]["prefixes"] = os.environ.get("COMMAND_PREFIXES") or "./!"
	cfg["customization"]["useSsh"] = False

	with open("config.ini", "w") as f:
		cfg.write(f)

	if os.environ.get("EXTRA_CONFIG"):
		with open("config.ini", "a") as f:
			f.write('\n' + os.environ.get("EXTRA_CONFIG"))

	if os.environ.get("PLUGINS"):
		for p in os.environ["PLUGINS"].split(","):
			install_plugin(p.strip())

	os.execv("python", os.getcwd() + "/" + bot.py)
