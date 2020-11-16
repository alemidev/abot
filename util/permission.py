import json

ALLOWED = {}

with open("perms.json") as f:
    ALLOWED = json.load(f)

def list_allowed():
    return list(ALLOWED.keys())

def is_allowed(sender_id):
    if sender_id is None:
        return False
    return sender_id in ALLOWED

def allow(uid):
    if uid in ALLOWED and ALLOWED[uid]:
        return False
    ALLOWED[uid] = True
    serialize()
    return True

def disallow(uid):
    if uid not in ALLOWED:
        return False
    ALLOWED.pop(uid, None)
    serialize()
    return True

def serialize():
    with open("perms.json", "w") as f:
        json.dump(ALLOWED, f)
