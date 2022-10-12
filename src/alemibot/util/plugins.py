import re
import os
import logging
import asyncio

from typing import Optional, List

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

def normalize_plugin_name(input_str:str) -> str:
	# TODO regexify maybe?
	if input_str.startswith('http'):
		input_str = input_str.split('://', 1)[1].split('/', 1)[1]
	if '@' in input_str:
		input_str = input_str.replace('.git', '').rsplit('@')[1]
	if '/' in input_str:
		input_str = input_str.rsplit('/', 1)[1]
	return input_str

def normalize_plugin_url(input_str:str) -> str:
	# TODO regexify maybe?
	if not input_str.startswith("https") and not input_str.startswith("git@"):
		input_str = f"https://github.com/{input_str}.git"
	return input_str

def normalize_plugin_name_author(url):
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
	res = stdout.decode()
	LOGGER.debug(res)
	if res.startswith(("ERROR", "fatal", "remote: Not Found")):
		return None
	match = REPO_HEAD_MATCHER.search(res)
	return match['branch'] if match else None

async def update_alemibot() -> bool:
	proc = await asyncio.create_subprocess_exec(
		"git", "pull",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	if b"Aborting" in stdout:
		raise GitException("Could not pull from remote")
	elif b"Already up to date" in stdout:
		 return False
	else:
		LOGGER.debug(stdout.decode())
		return True

async def install_plugin(plugin:str, path:str=None, branch:str=None):
	url = normalize_plugin_url(plugin)
	args = ["git", "submodule", "add" ]
	if branch:
		args.append("-b")
		args.append(branch)
	args.append(url)
	if path:
		args.append(path)
	else:
		args.append(f"plugins/{normalize_plugin_name(plugin)}")
	proc = await asyncio.create_subprocess_exec(
		*args,
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT,
		env={ "GIT_TERMINAL_PROMPT" : "0" },
	)
	stdout, _stderr = await proc.communicate()
	res = stdout.decode()
	if "ERROR: Repository not found" in res:
		raise RepositoryNotExistingException(res)
	if re.search(r"fatal: '(.*)' is not a commit", res):
		raise BranchNotExistingException(res)
	if "fatal" in res or not res.startswith("Cloning"):
		LOGGER.error(res)
		raise GitException(f"clone of '{url}' failed")
	LOGGER.debug(res)

async def update_plugins() -> int:
	if not os.path.isfile(".gitmodules"):
		return 0
	sub_proc = await asyncio.create_subprocess_exec(
		"git", "submodule", "update", "--remote",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await sub_proc.communicate()
	LOGGER.debug(stdout.decode())
	return stdout.count(b"checked out")

async def remove_plugin(plugin:str, dependancies:bool=False) -> bool:
	plugin = normalize_plugin_name(plugin)
	proc = await asyncio.create_subprocess_exec(
		"git", "submodule", "deinit", "-f", f"plugins/{plugin}",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	LOGGER.debug(stdout.decode())
	if not stdout.startswith(b"Cleared"):
		return False
	proc = await asyncio.create_subprocess_exec(
		"rm", "-rf", f".git/modules/plugins/{plugin}",
	)
	proc = await asyncio.create_subprocess_exec(
		"git", "rm", "-f", f"plugins/{plugin}",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	LOGGER.debug(stdout.decode())
	if b"rm 'plugins/" not in stdout:
		return False
	return True

async def install_dependancies(plugin:str) -> int:
	plugin = normalize_plugin_name(plugin)
	if not os.path.isfile(f"plugins/{plugin}/requirements.txt"):
		return 0
	proc = await asyncio.create_subprocess_exec(
		"pip", "install", "-r", f"plugins/{plugin}/requirements.txt", "--upgrade",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	res = stdout.decode()
	if b"ERROR" in stdout:
		LOGGER.error(res)
		raise PipException(res)
	return res.count('Uninstalling')  # TODO why did I decide to count 'Uninstalling' ?!??!

async def update_alemibot_dependancies() -> int:
	proc = await asyncio.create_subprocess_exec(
		"pip", "install", ".", "--upgrade",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	LOGGER.debug(stdout.decode())
	if b"ERROR" in stdout:
		raise PipException("Some dependancies raised errors while upgrading")
	return stdout.count(b'Collecting')

async def update_plugins_dependancies() -> int:
	with open(".gitmodules") as f:
		modules = f.read()
	matches = re.findall(r"path = (?P<path>plugins/[^ ]+)\n", modules)
	count = 0
	for match in matches:
		if os.path.isfile(f"{match}/requirements.txt"):
			proc = await asyncio.create_subprocess_exec(
				"pip", "install", "-r", f"{match}/requirements.txt", "--upgrade",
				stdout=asyncio.subprocess.PIPE,
				stderr=asyncio.subprocess.STDOUT
			)
			stdout, _stderr = await proc.communicate()
			LOGGER.debug(stdout.decode())
			count += stdout.count(b'Collecting')
	return count

async def remove_dependancies(plugin:str) -> int:
	plugin = normalize_plugin_name(plugin)
	if not os.path.isfile(f"plugins/{plugin}/requirements.txt"):
		return 0

	proc = await asyncio.create_subprocess_exec(
		"pip", "uninstall", "-y", "-r", f"plugins/{plugin}/requirements.txt",
		stdout=asyncio.subprocess.PIPE,
		stderr=asyncio.subprocess.STDOUT
	)
	stdout, _stderr = await proc.communicate()
	LOGGER.debug(stdout.decode())
	if b"ERROR" in stdout:
		return 0
	return stdout.count(b'Uninstalling')

def has_plugins() -> bool:
	return os.path.isfile(".gitmodules")

def get_plugin_list() -> List[str]:
	if os.path.isfile(".gitmodules"):
		with open(".gitmodules") as f:
			modules = f.read()
		return GITMODULE_URL_MATCHER.findall(modules)
	return []

