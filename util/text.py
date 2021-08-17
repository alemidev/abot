import re
import shutil

from typing import Dict
from logging import Formatter, LogRecord, DEBUG, INFO, WARNING, ERROR, CRITICAL

from termcolor import colored

class ColorFormatter(Formatter):
	def __init__(self, fmt:str):
		self.fmt : str = fmt
		self.formatters : Dict[int, Formatter] = {
			DEBUG: Formatter(colored(fmt, color='grey')),
			INFO: Formatter(colored(fmt, color='white')),
			WARNING: Formatter(colored(fmt, color='yellow')),
			ERROR: Formatter(colored(fmt, color='red')),
			CRITICAL: Formatter(colored(fmt, color='red', attrs=['bold'])),
		}

	def format(self, record:LogRecord) -> str:
		return self.formatters.get(record.levelno).format(record)

def cleanhtml(raw_html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_html)
	return cleantext

def cleartermcolor(raw_in):
	ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
	return ansi_escape.sub('', raw_in)

def order_suffix(num, measure='B'):
	for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
		if abs(num) < 1024.0:
			return "{n:3.1f} {u}{m}".format(n=num, u=unit, m=measure)
		num /= 1024.0
	return "{n:.1f} Yi{m}".format(n=num, m=measure)

def sep(num, sep=" "): # python lacks a better way to set thousands separator afaik! (without messing with locale)
	return "{n:,}".format(n=num).replace(",", sep)
	
def tokenize_json(text):
	res = re.subn(
		r'("[^\"]+"|[0-9.\-]+)',
		r'``\g<1>``', text.strip())
	if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
		return tokenize_lines(text) # try to tokenize per line at least
	return "`" + res[0] + "`"

def tokenize_lines(text, mode='markdown'):
	BEFORE = "```" if mode == "markdown" else "<code>"
	AFTER = "```" if mode == "markdown" else "</code>"
	res =  re.subn(r'(.+)', BEFORE + r'\g<1>' + AFTER, text.strip())
	if res[1] * 2 > 100: # we generate 2 entities for every replace we do (kinda)
		return BEFORE + text + AFTER
	return res[0]

def split_for_window(text, offset=0):
	width = shutil.get_terminal_size((100, 100))[0] # pass a fallback, 1st arg is width
	width -= width//10 # pad by 1/10th
	text = text.replace("\n", "\n" + " "*offset)
	buf = text.split(" ")
	out = ""
	line = ""
	cap = width - offset
	for w in buf:
		if len(line + " " + w) > cap:
			if len(w) > cap: # word wouldn't fit anyway
				line += " " + w
				while len(line) > cap:
					out += line[:cap] + "\n" + " "*offset
					line= line[cap:]
				continue
			else:
				out += line + "\n" + " "*offset
				line = ""
		line += w + " "
	out += line
	return out