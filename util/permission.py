import json

ALLOWED = {}
# Damn JSON won't allow integer keys, so we str() everything

with open("perms.json") as f:
    ALLOWED = json.load(f)

def list_allowed():
    return list(ALLOWED.keys())

def is_allowed(sender_id):
    if sender_id is None:
        return False
    return str(sender_id) in ALLOWED

def allow(uid, val=True):
    if uid in ALLOWED and ALLOWED[uid] == val:
        return False
    ALLOWED[str(uid)] = val # this is handy when editing manually the file
    serialize()
    return True

def disallow(uid):
    if str(uid) not in ALLOWED:
        return False
    ALLOWED.pop(str(uid), None)
    serialize()
    return True

def serialize():
    with open("perms.json", "w") as f:
        json.dump(ALLOWED, f)
