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
    ALLOWED[uid] = True
    serialize()

def disallow(uid):
    ALLOWED.pop(uid, None)
    serialize()

def serialize():
    with open("perms.json", "w") as f:
        json.dump(ALLOWED, f)
