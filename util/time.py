import re
from datetime import timedelta

def _search_value(text, token):
	val = 0
	res = re.search(rf"(?P<sign>\+|\-|)(?P<val>[0-9]+)(?: |){token}", text)
	if res:
		val = int(res["val"])
		if res["sign"] == "-":
			val = -val
	return val


def parse_timedelta(text):
	"""Convert string into timedelta

	Will convert a string to a timedelta object. Will parse by
	searching numbers with time suffixes in the given string, for
	example 1h, 12min32s and 2y40d. Will also match sign (+|-|)
	If input is just an integer, it will be treated as number of seconds
	"""
	if text.isnumeric():
		return timedelta(seconds=int(text))
	year = _search_value(text, "y")
	day = _search_value(text, "d")
	hour = _search_value(text, "h")
	minute = _search_value(text, "m")
	second = _search_value(text, "s")
	return timedelta(days=(day+(year*365)),
					 hours=hour,
					 minutes=minute,
					 seconds=second)

