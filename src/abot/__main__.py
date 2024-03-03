import os
import argparse
import logging
from logging.handlers import RotatingFileHandler

from setproctitle import setproctitle

from .bot import aBot
from .util.text import setup_logging

if __name__ == "__main__":
	"""
	Default logging will only show the message on stdout (but up to INFO) 
	and show time + type + module + message in file (data/<name>.log)
	"""
	setproctitle("aBot")

	parser = argparse.ArgumentParser(
		prog='python -m abot',
		description='aBot | Telegram (user)bot framework',
	)

	parser.add_argument('name', help='name to use for this client session')
	parser.add_argument('--config', dest='config', metavar='PATH', type=str, default=None, help='specify path for config file (default <name>.ini in cwd)')

	parser.add_argument('--api-id', dest='api_id', type=int, help="API ID to use for authentication, overrides config")
	parser.add_argument('--api-hash', dest='api_hash', help="API HASH to use for authentication, overrides config")
	parser.add_argument('--session', dest='session_string', metavar='STRING', help='use given pre-authenticated session string for login')
	parser.add_argument('--install', dest='install', metavar='PLUGIN', nargs='+', help='install requested plugins at first startup')
	parser.add_argument('--prefix', dest='prefixes', help="prefixes for commands (each character is a distinct one)")
	parser.add_argument('--sudo', dest='sudo', metavar="UID", type=int, nargs='+', help="user ids of those allowed to operate as owners, overrides config")
	parser.add_argument('--allow-plugins', dest='allow_plugins', action='store_const', const=True, default=False, help="allow sudoers to install plugins (git submodules)")
	parser.add_argument('--no-color', dest='color', action='store_const', default=True, const=False, help='disable colors for logger text')
	parser.add_argument('--debug', dest='debug_level', action='store_const', default=logging.INFO, const=logging.DEBUG, help='Set logging to debug level')

	args = parser.parse_args()

	if not os.path.isdir('data'):
		os.mkdir('data')
	if not os.path.isdir('log'):
		os.mkdir('log')

	setup_logging(args.name, level=args.debug_level, color=args.color)

	kwargs = {}
	if args.api_id is not None:
		kwargs["api_id"] = args.api_id
	if args.api_hash is not None:
		kwargs["api_hash"] = args.api_hash
	if args.session_string is not None:
		kwargs["session_string"] = args.session_string

	app = aBot(
		args.name,
		config_file=args.config,
		allow_plugins=args.allow_plugins,
		sudoers=[ int(x) for x in args.sudo ] if args.sudo is not None else None,
		prefixes=list(args.prefixes) if args.prefixes is not None else None,
		install=args.install or [],
		**kwargs
	)

	app.run()

