import re
import os
import logging
import asyncio

from typing import Optional, List

from alemibot.bot import alemiBot
from alemibot.util import cleartermcolor, is_me, get_username, edit_or_reply
from alemibot.util.command import _Message as Message
from alemibot.patches import DocumentFileStorage

LOGGER = logging.getLogger("GIT")

REPO_HEAD_MATCHER = re.compile(r"refs\/heads\/(?P<branch>[^\s]+)(?:\s+)HEAD")
GITMODULE_URL_MATCHER = re.compile(r"url = (git@github.com:|https://github.com/)(?P<module>.*).git")

PLUGIN_HTTPS = re.compile(r"http(?:s|):\/\/(?:.*)\/(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")
PLUGIN_SSH = re.compile(r"git@(?:.*)\.(?:.*):(?P<author>[^ ]+)\/(?P<plugin>[^ \.]+)(?:\.git|)")

class PipException(Exception):
	pass

class GitException(Exception):
	pass

class BranchNotExistingException(GitException):
	pass

class RepositoryNotExistingException(GitException):
	pass

def split_url(url):
	match = PLUGIN_HTTPS.match(url)
	if match:
		return match["plugin"], match["author"]
	match = PLUGIN_SSH.match(url)
	if match:
		return match["plugin"], match["author"]
	author, plugin = url.split("/", 1)
	return plugin, author

async def get_repo_head(repo:str) -> Optional[str]:
	proc = await asyncio.create_subprocess_exec(
		"git", "ls-remote", "--symref", repo, "HEAD",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT,
		env={ "GIT_TERMINAL_PROMPT" : "0" },
	)
	stdout, _sterr = await proc.communicate()
	res = cleartermcolor(stdout.decode())
	LOGGER.debug(res)
	if res.startswith(("ERROR", "fatal", "remote: Not Found")):
		return None
	match = REPO_HEAD_MATCHER.search(res)
	return match['branch'] if match else None

async def install_plugin(plugin:str, path:str=None, branch:str=None):
	if not plugin.startswith("https") and not plugin.startswith("git@"):
		plugin = f"https://github.com/{plugin}.git"
	args = ["git", "submodule", "add" ]
	if branch:
		args.append("-b")
		args.append(branch)
	args.append(plugin)
	if path:
		args.append(path)
	proc = await asyncio.create_subprocess_exec(
		*args,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT,
		env={ "GIT_TERMINAL_PROMPT" : "0" },
	)
	stdout, _stderr = await proc.communicate()
	res = cleartermcolor(stdout.decode())
	if not res.startswith("Cloning"):
		LOGGER.error(res)
		raise GitException(res)
	if "ERROR: Repository not found" in res:
		raise RepositoryNotExistingException(res)
	if re.search(r"fatal: '(.*)' is not a commit", res):
		raise BranchNotExistingException(res)
	LOGGER.debug(res)

async def install_dependancies(plugin:str) -> int:
	proc = await asyncio.create_subprocess_exec(
		"pip", "install", "-r", f"plugins/{plugin}/requirements.txt", "--upgrade",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	res = cleartermcolor(stdout)
	if b"ERROR" in stdout:
		LOGGER.error(res)
		raise PipException(res)
	return res.count('Uninstalling')  # TODO why did I decide to count 'Uninstalling' ?!??!

def get_plugin_list() -> List[str]:
	if os.path.isfile(".gitmodules"):
		with open(".gitmodules") as f:
			modules = f.read()
		return GITMODULE_URL_MATCHER.findall(modules)
	return []

