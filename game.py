import threading
import configparser
from queue import Queue
from pyboy import PyBoy


key_map = {
    'UP': 'up',
    'DOWN': 'down',
    'LEFT': 'left',
    'RIGHT': 'right',
    'A': 'a',
    'B': 'b',
    'START': 'start',
    'SELECT': 'select',
}

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Default to False if 'cli' isn't found in the config file
    return config.getboolean('Settings', 'cli', fallback=False)

def get_inputs(command_queue):
    while True:
        get_input(command_queue)

def get_input(command_queue=None):
    command = input("Enter command (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT) or 'exit' to quit: ").upper()

    if command == 'EXIT':
        command_queue.put('EXIT')
        return

    if command in key_map:
        button = key_map[command]
        command_queue.put(button)

def start():
    pyboy = PyBoy('emulation/red.gb')
    command_queue = Queue()
    cli = read_config()

    if cli:
        input_thread = threading.Thread(target=get_inputs, args=(command_queue,), daemon=True)
        input_thread.start()


    while pyboy.tick():
        if not command_queue.empty():
            command = command_queue.get()
            if command == 'EXIT':
                break
            pyboy.button(command)
        pass
    pyboy.stop()


    
if __name__ == "__main__":
    start()