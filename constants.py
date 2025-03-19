import random

key_map = {
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
    "A": "a",
    "B": "b",
    "START": "start",
    "SELECT": "select",
}

def get_random_key(key_map):
    return random.choice(list(key_map.keys()))