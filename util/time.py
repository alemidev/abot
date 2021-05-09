import re
from datetime import timedelta

def parse_timedelta(text):
	"""
	Will convert a string to a timedelta object. Will parse by
	searching numbers with time suffixes in the given string, for
	example 1h, 12min32s and 2y40d
	"""
	year = 0
	res = re.search("(?P<val>[0-9]+)(?: |)y", text)
	if res:
		year = int(res["val"])
	day = 0
	res = re.search("(?P<val>[0-9]+)(?: |)d", text)
	if res:
		day = int(res["val"])
	hour = 0
	res = re.search("(?P<val>[0-9]+)(?: |)h", text)
	if res:
		hour = int(res["val"])
	minute = 0
	res = re.search("(?P<val>[0-9]+)(?: |)m", text)
	if res:
		minute = int(res["val"])
	second = 0
	res = re.search("(?P<val>[0-9]+)(?: |)s", text)
	if res:
		second = int(res["val"])
	return timedelta(days=(day+(year*365)),
					 hours=hour,
					 minutes=minute,
					 seconds=second)

