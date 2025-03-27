import threading
from config import read_config
from queue import Queue
from pyboy import PyBoy
import time
from constants import key_map
from game_service import MockGameService, HTTPGameService


class GameInstance:
    def __init__(self, rom_path):
        self.pyboy = PyBoy(gamerom=rom_path, sound_emulated=False)
        self.command_queue = Queue(maxsize=100) # Agent commands. The agent may chain commands.
        self.data_queue = Queue(maxsize=1) # Game data for the agent to act on.
        self.input_thread = None
        self.output_thread = None
        self.image = None
        self.image_lock = threading.Lock()
        self.capture_speed = read_config(
            "Settings", "capture_speed", default=5, value_type=int
        )

    def run(self):
        game_speed = read_config("Settings", "game_speed", default=1, value_type=int)
        self.pyboy.set_emulation_speed(target_speed=game_speed)
        self.start_output_thread()
        while self.pyboy.tick():
            if not self.command_queue.empty():
                command = self.read_command()
                if command == "EXIT":
                    break
                self.pyboy.button(command)

        self.pyboy.stop()

    def read_command(self):
        command = self.command_queue.get()
        if command == "EXIT":
            return command

        if command in key_map:
            return command

        raise ValueError(f"Invalid command: {command}")

    def start_output_thread(self):
        self.output_thread = threading.Thread(target=self.capture_image, daemon=True)
        self.output_thread.start()

    def capture_image(self):
        while True:
            time.sleep(self.capture_speed)
            if self.data_queue.empty():
                with self.image_lock:
                    self.image = self.pyboy.screen.image.copy()
                self.data_queue.put(
                    (self.image, self.pyboy.game_wrapper.game_area_collision())
                )

    def get_output(self):
        return self.image, self.pyboy.game_wrapper.game_area_collision()


def get_game_service(game: GameInstance):
    mock_service = read_config("Settings", "mock_service", default=True, value_type=bool)
    return (
        MockGameService(game.command_queue, game.data_queue)
        if mock_service
        else HTTPGameService(game.command_queue, game.data_queue)
    )


if __name__ == "__main__":
    gamefile = read_config("Settings", "gamefile", default="emulation/game.gb")
    mock_service = read_config("Settings", "mock", default=True, value_type=bool)
    game = GameInstance(gamefile)
    game_service = get_game_service(game)
    threading.Thread(target=game_service.start_game, daemon=True).start()
    game.run()
