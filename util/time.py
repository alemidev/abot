import re
from datetime import timedelta

def parse_timedelta(text):
    # Oh my this part is horrible but should work reliably
    year = 0
    res = re.search("(?P<val>[0-9])(?: |)y", text)
    if res:
        year = int(res["val"])
    day = 0
    res = re.search("(?P<val>[0-9])(?: |)d", text)
    if res:
        day = int(res["val"])
    hour = 0
    res = re.search("(?P<val>[0-9])(?: |)h", text)
    if res:
        hour = int(res["val"])
    minute = 0
    res = re.search("(?P<val>[0-9])(?: |)m", text)
    if res:
        minute = int(res["val"])
    second = 0
    res = re.search("(?P<val>[0-9])(?: |)s", text)
    if res:
        second = int(res["val"])
    return timedelta(days=(day+(year*365)),
                     hours=hour,
                     minutes=minute,
                     seconds=second)

