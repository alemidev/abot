import typing
from datetime import datetime

from pyrogram.types import List

def convert_to_dict(obj, depth=0):
    if depth > 10: # safety recursion stop
        print(f"[!] Terminating recursion : {str(obj)}")
        return str(obj)
    if isinstance(obj, datetime) or isinstance(obj, int) \
    or isinstance(obj, float) or isinstance(obj, bool) or obj is None:
        return obj 
    elif isinstance(obj, list) or isinstance(obj, List):
        return [ convert_to_dict(e, depth=depth+1) for e in obj ]
    elif not hasattr(obj, "__dict__"):
        return str(obj)
    elif isinstance(obj, str): # The weird Str thing from pyrogram
        return {
            "raw" : str(obj),
            "markdown" : obj.markdown,
            "html" : obj.html
        }
    else:
        return {
            "_": obj.__class__.__name__,
            **{
                attr: (
                    "*" * len(getattr(obj, attr))
                    if attr == "phone_number" else
                    datetime.fromtimestamp(getattr(obj, attr))
                    if attr.endswith("date") else
                    convert_to_dict(getattr(obj, attr), depth=depth+1)
                )
                for attr in filter(lambda x: not x.startswith("_"), obj.__dict__)
                if getattr(obj, attr) is not None
            }
        }
