#!/usr/bin/env python
"""
"""
import re
import os
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler

from bot import alemiBot

from util.text import cleartermcolor

from plugins.core import split_url

def install_plugin(user_input):
	try:
		plugin, author = split_url(user_input) # clear url or stuff around
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
		res = cleartermcolor(stdout.decode())
		logger.info(res)
		if res.startswith(("ERROR", "fatal", "remote: Not Found")):
			logger.error("Could not find %s", link)
			return
		branch = re.search(r"(?:.*)\tHEAD\n(?:.*)\trefs/heads/(?P<branch>.*)\n", res)["branch"]

		logger.info("Fetching source code")

		proc = subprocess.Popen(
		  ["git", "submodule", "add", "-b", branch, link, f"plugins/{folder}"],
		  stdout=subprocess.PIPE,
		  stderr=subprocess.STDOUT,
		  env=custom_env)

		stdout, _sterr = proc.communicate()
		res = cleartermcolor(stdout.decode())
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
	"""
	Default logging will only show the message on stdout (but up to INFO) 
	and show time + type + module + message in file (data/debug.log)
	"""
	logger = logging.getLogger()
	logger.setLevel(logging.INFO)
	# create file handler which logs even debug messages
	fh = RotatingFileHandler('data/debug.log', maxBytes=1048576, backupCount=5) # 1MB files
	fh.setLevel(logging.INFO)
	# create console handler with a higher log level
	ch = logging.StreamHandler()
	ch.setLevel(logging.INFO)
	# create formatter and add it to the handlers
	file_formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s", "%b %d %Y %H:%M:%S")
	print_formatter = logging.Formatter("> %(message)s")
	fh.setFormatter(file_formatter)
	ch.setFormatter(print_formatter)
	# add the handlers to the logger
	logger.addHandler(fh)
	logger.addHandler(ch)

	if "CONFIG" in os.environ:
		with open("config.ini", "w") as f:
			f.write(os.environ["CONFIG"])

	if "PLUGINS" in os.environ:
		for p in os.environ["PLUGINS"].split(","):
			install_plugin(p.strip())

	app = alemiBot(
		os.environ["SESSION_STRING"],
		api_id=os.environ["API_ID"],
		api_hash=os.environ["API_HASH"],
		plugins=dict(root="plugins"),
	)
	app.run()

