import threading
from config import read_config
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
        self.pyboy = PyBoy(rom_path)
        self.command_queue = Queue()
        self.input_thread = None

    # TODO: remove CLI option when Agent is implemented
    def get_inputs(self):
        while True:
            self.get_input()

    def get_input(self):
        command = input(
            "Enter command (UP, DOWN, LEFT, RIGHT, A, B, START, SELECT) or 'exit' to quit: "
        ).upper()

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

    def run(self):
        self.start_input_thread()

        while self.pyboy.tick():
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == "EXIT":
                    break
                self.pyboy.button(command)

        self.pyboy.stop()


if __name__ == "__main__":
    gamefile = read_config("Settings", "gamefile", default="emulation/game.gb")
    game = GameInstance(gamefile)
    game.run()
