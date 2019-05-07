import random

def dbg(str = None):
    if str is None:
        strs=["hello","bite","cul","merde","sa race"]
        print(random.choice(strs))
    else:
        print(str)
