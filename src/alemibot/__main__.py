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

	args = parser.parse_args()

	setup_logging(args.name, args.color)

	if not os.path.isdir('data'):
		os.mkdir('data')
	if not os.path.isdir('log'):
		os.mkdir('log')

	app = alemiBot(args.name)

	app.run()

