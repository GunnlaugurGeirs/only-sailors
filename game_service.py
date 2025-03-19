
from queue import Queue
import time
import threading
from constants import key_map, get_random_key
from config import read_config

class GameService:
    def __init__(self, command_queue: Queue, output_queue: Queue):
        self.command_queue = command_queue
        self.output_queue = output_queue

    def start_game(self):
        threading.Thread(target=self.simulate_input, daemon=True).start()
        threading.Thread(target=self.simulate_output, daemon=True).start()

    # TODO: replace simulated calls with calls to ollama
    def simulate_input(self):
        while True:
            key = get_random_key(key_map)
            self.command_queue.put(key)
            time.sleep(1)

    def simulate_output(self):
        while True:
            image, collision = self.output_queue.get()
            time.sleep(5)


    