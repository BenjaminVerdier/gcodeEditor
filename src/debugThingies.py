import random

def dbg(dbgStr = None):
    if dbgStr is None:
        strs=["hello","bite","cul","merde","sa race"]
        dbgStr = random.choice(strs)
    print("DEBUG: " + str(dbgStr))
