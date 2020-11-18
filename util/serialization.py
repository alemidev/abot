import typing
from datetime import datetime

def convert_to_dict(obj):
    if not hasattr(obj, "__dict__"):
        return obj
    if isinstance(obj, str): # The weird Str thing from pyrogram
        return {
            "raw" : str(obj),
            "markdown" : obj.markdown,
            "html" : obj.html
        }
    return {
        "_": obj.__class__.__name__,
        **{
            attr: (
                "*" * len(getattr(obj, attr))
                if attr == "phone_number" else
                datetime.fromtimestamp(getattr(obj, attr))
                if attr.endswith("date") else
                convert_to_dict(getattr(obj, attr))
            )
            for attr in filter(lambda x: not x.startswith("_"), obj.__dict__)
            if getattr(obj, attr) is not None
        }
    }
