import random

key_map = (
    "up",
    "down",
    "left",
    "right",
    "a",
    "b",
    "start",
    "select",
)

def get_random_key():
    return random.choice(list(key_map))
