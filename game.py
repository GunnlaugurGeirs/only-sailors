import threading
import time
from config import read_config
from memory_utils import get_pokemon_name, get_first_pokemon_info
from queue import Queue
from pyboy import PyBoy

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

class GameInstance:
    def __init__(self, rom_path):
        self.pyboy = PyBoy(gamerom=rom_path, sound_volume=0)
        self.command_queue = Queue()
        self.input_thread = None
        self.output_thread = None
        self.image = None
        self.image_lock = threading.Lock()

    def run(self):
        self.start_input_thread()
        self.start_output_thread()
        while self.pyboy.tick():
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == "EXIT":
                    break
                self.pyboy.button(command)

        self.pyboy.stop()

    # TODO: remove CLI option when Agent is implemented
    def get_inputs(self):
        while True:
            self.get_input()

    def get_input(self):
        command = input(
            "Enter command (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT) or 'exit' to quit: "
        ).upper()

        self.command(command)

    def command(self, command):
        if command == "EXIT":
            self.command_queue.put("EXIT")
            return

        if command in key_map:
            button = key_map[command]
            self.command_queue.put(button)

    def start_input_thread(self):
        cli = read_config("Settings", "cli", default=False, value_type=bool)
        if cli:
            self.input_thread = threading.Thread(
                target=self.get_inputs, args=(), daemon=True
            )
        else:
            self.input_thread = threading.Thread(
                target=self.get_input, args=(), daemon=True
            )
        self.input_thread.start()
    
    def start_output_thread(self):
        self.output_thread = threading.Thread(target=self.capture_image, daemon=True)
        self.output_thread.start()

    def capture_image(self):
        while True:
            with self.image_lock: 
                self.image = self.pyboy.screen.image.copy()
                print(get_pokemon_name(self.pyboy))
                print(get_first_pokemon_info(self.pyboy))
            time.sleep(read_config("Settings", "capture_time", default=5, value_type=int))

    def get_output(self):
        return self.image, self.pyboy.game_wrapper.game_area_collision()

if __name__ == "__main__":
    gamefile = read_config("Settings", "gamefile", default="emulation/game.gb")
    game = GameInstance(gamefile)
    game.run()
