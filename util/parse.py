import re

class CommandParser:
    def __init__(self, opts, flags=None):
        self.opts = opts
        self.flags = flags

    def parse(self, command):
        cmd = list(command) # make a copy
        cmd.pop(0) # first element is always the command itself
        res = {}
        if self.flags is not None:
            res["flags"] = []
            i = 0
            while i < len(cmd):
                if cmd[i] in self.flags:
                    res["flags"].append(cmd.pop(i))
                else: # don't increase because next token now have same index as before
                    i +=1
        for o in self.opts: # for every option to search
            for i in range(len(cmd)):
                if cmd[i] in self.opts[o]: # if keyword is matched, consume it and next argument
                    cmd.pop(i)
                    res[o] = cmd.pop(i) # it shifted 1 down
                    break
        if len(cmd) > 0: # not everything was consumed
            res["arg"] = " ".join(cmd)
        return res

def cleanhtml(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def cleartermcolor(raw_in):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', raw_in)

