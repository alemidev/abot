import os
import argparse
import logging
from logging.handlers import RotatingFileHandler

from setproctitle import setproctitle

from .bot import alemiBot
from .util.text import setup_logging

if __name__ == "__main__":
	"""
	Default logging will only show the message on stdout (but up to INFO) 
	and show time + type + module + message in file (data/<name>.log)
	"""
	setproctitle("alemiBot")

	parser = argparse.ArgumentParser(
		prog='python -m alemibot',
		description='alemiBot | My personal Telegram (user)bot framework',
	)

	parser.add_argument('name', help='name to use for this client session')
	parser.add_argument('--no-color', dest='color', action='store_const', default=True, const=False, help='disable colors for logger text')
	parser.add_argument('--debug', dest='debug_level', action='store_const', default=logging.INFO, const=logging.DEBUG, help='Set logging to debug level')

	args = parser.parse_args()

	if not os.path.isdir('data'):
		os.mkdir('data')
	if not os.path.isdir('log'):
		os.mkdir('log')

	setup_logging(args.name, level=args.debug_level, color=args.color)

	app = alemiBot(args.name)

	app.run()

