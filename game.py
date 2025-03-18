import threading
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

def get_input(command_queue):
    while True:
        command = input("Enter command (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT) or 'exit' to quit: ").upper()

        if command == 'EXIT':
            command_queue.put('EXIT')
            break

        if command in key_map:
            button = key_map[command]
            command_queue.put(button)

def start():
    pyboy = PyBoy('emulation/red.gb')
    command_queue = Queue()
    input_thread = threading.Thread(target=get_input, args=(command_queue,), daemon=True)
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