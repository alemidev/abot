import re

from typing import Dict, List
from pyrogram.types import Message
from pyrogram.filters import create

def filterCommand(commands: str or List[str], prefixes: str or List[str] = "/",
            options: Dict[str, List[str]] = {}, flags: List[str] = [], case_sensitive: bool = False):
    """Filter commands, i.e.: text messages starting with "/" or any other custom prefix.
    Parameters:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *command*
            field of the :obj:`~pyrogram.types.Message`.
        prefixes (``str`` | ``list``, *optional*):
            A prefix or a list of prefixes as string the filter should look for.
            Defaults to "/" (slash). Examples: ".", "!", ["/", "!", "."], list(".:!").
            Pass None or "" (empty string) to allow commands with no prefix at all.
        options (``dict { str : list }``, *optional*):
            A dictionary with name and list of keywords to match. If a keyword is matched 
            in the commands, it will be consumed together with next element and put in the 
            resulting "options" dict for ease of access. Examples : { "time": ["-t"] }
        flags (``list``, *optional*):
            A list of flags to search in the commands. If an element equals a flag given, it 
            will be consumed and put in the resulting "flags" list. Example : [ "-list" ]
        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, command="Start" would trigger /Start but not /start.
    """
    command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

    async def func(flt, client, message: Message):
        text = message.text or message.caption
        message.command = None

        if not text:
            return False

        pattern = r"^{cmd}(?:@{uname}|)(?:\s|$)" if flt.case_sensitive else r"(?i)^{cmd}(?:@{uname}+|)(?:\s|$)"

        for prefix in flt.prefixes:
            if not text.startswith(prefix):
                continue

            without_prefix = text[len(prefix):]

            for cmd in flt.commands:
                if not re.match(pattern.format(cmd=re.escape(cmd), uname=client.me.username), without_prefix):
                    continue

                without_cmd = re.sub("^@[^ ]+(?: |)", "", without_prefix[len(cmd):])
                # match.groups are 1-indexed, group(1) is the quote, group(2) is the text
                # between the quotes, group(3) is unquoted, whitespace-split text

                # Remove the escape character from the arguments
                match_list = [
                    re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                    for m in command_re.finditer(without_cmd)
                ]
                
                raw_buf = without_cmd

                message.command = { "flags" : [],
                                    "base" : cmd }

                i = 0
                while i < len(match_list):
                    if match_list[i] in flt.flags:
                        token = match_list.pop(i)
                        raw_buf = raw_buf.replace(token, "")
                        message.command["flags"].append(token)
                        continue
                    op = False
                    for k in flt.options:
                        if match_list[i] in flt.options[k]:
                            op = True
                            raw_buf = raw_buf.replace(match_list.pop(i), "") # most importantly, pop one token!
                            message.command[k] = match_list.pop(i)
                            raw_buf = raw_buf.replace(message.command[k], "")
                            break
                    if not op:
                        i +=1

                if len(match_list) > 0:
                    message.command["cmd"] = match_list # everything not consumed
                    message.command["arg"] = " ".join(match_list) # provide a joined argument already
                message.command["raw"] = re.sub(' +', ' ', raw_buf.replace('""', '')).strip()

                return True

        return False

    commands = commands if isinstance(commands, list) else [commands]
    commands = {c if case_sensitive else c.lower() for c in commands}

    prefixes = [] if prefixes is None else prefixes
    prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
    prefixes = set(prefixes) if prefixes else {""}

    flags = flags if isinstance(flags, list) else [flags]

    for k in options:
        options[k] = options[k] if isinstance(options[k], list) else [options[k]]


    return create(
        func,
        "CommandFilter",
        commands=commands,
        prefixes=prefixes,
        case_sensitive=case_sensitive,
        options=options,
        flags=flags
    )
