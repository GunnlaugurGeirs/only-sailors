from pyboy import PyBoy

def read_m(pyboy: PyBoy, addr) -> int:
        return pyboy.memory[addr]


def map_char(b) -> chr:
    if b == 0x50:  # Terminator byte
        return None
    # Handle different character ranges
    if 0x80 <= b <= 0x99:  # Uppercase A-Z
        return chr(ord('A') + (b - 0x80))
    elif 0xA0 <= b <= 0xB9:  # Lowercase a-z
        return chr(ord('a') + (b - 0xA0))
    elif b == 0xBA:  # é
        return 'é'
    elif 0xE0 <= b <= 0xE9:  # Digits 0-9
        return str(b - 0xE0)
    elif b == 0xEA:  # '!'
        return '!'
    elif b == 0xEB:  # '?'
        return '?'
    elif b == 0xEC:  # '.'
        return '.'
    elif b == 0xED:  # '-'
        return '-'
    elif b == 0x7F or b == 0x00:  # Space or control character
        return ' '
    else:
        return '?'


def get_pokemon_name(pyboy):
    party_count = read_m(pyboy, 0xD163)
    if party_count == 0:
        return ""
    
    nickname_address = 0xD2B5
    nickname_bytes = [read_m(pyboy, nickname_address + i) for i in range(11)]
    
    nickname = []
    for b in nickname_bytes[:10]:
        char = map_char(b)
        nickname.append(char)
    
    return ''.join(nickname)


def get_first_pokemon_info(pyboy):
    party_count = read_m(pyboy, 0xD163)
    if party_count == 0:
        return {
            "species": 0,
            "level": 0,
            "nickname": "",
            "current_hp": 0,
            "max_hp": 0
        }
    
    # Species (1 byte at D16B)
    species = read_m(pyboy, 0xD16B)
    
    # Level (1 byte at D18C)
    level = read_m(pyboy, 0xD18C)
    
    # Current HP (little-endian, 2 bytes at D16C-D16D)
    current_hp_low = read_m(pyboy, 0xD16C)
    current_hp_high = read_m(pyboy, 0xD16D)
    current_hp = (current_hp_high << 8) | current_hp_low
    
    # Max HP (little-endian, 2 bytes at D186-D187)
    max_hp_low = read_m(pyboy, 0xD186)
    max_hp_high = read_m(pyboy, 0xD187)
    max_hp = (max_hp_high << 8) | max_hp_low
    
    # Nickname (11 bytes starting at D2B5)
    nickname_address = 0xD2B5
    nickname_bytes = [read_m(pyboy, nickname_address + i) for i in range(11)]
    
    nickname = []
    for b in nickname_bytes[:10]:  # Process up to 10 characters
        char = map_char(b)
        if char is None:  # Terminator encountered
            break
        nickname.append(char)
    nickname_str = ''.join(nickname)
    
    return {
        "species": species,
        "level": level,
        "nickname": nickname_str,
        "current_hp": current_hp,
        "max_hp": max_hp
    }