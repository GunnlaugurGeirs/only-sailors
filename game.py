import threading
from config import read_config
from queue import Queue
from pyboy import PyBoy
from constants import key_map
from game_service import GameService

class GameInstance:
    def __init__(self, rom_path):
        self.pyboy = PyBoy(gamerom=rom_path, sound_emulated=False)
        self.command_queue = Queue()
        self.output_queue = Queue(maxsize=1)
        self.input_thread = None
        self.output_thread = None
        self.image = None
        self.image_lock = threading.Lock()

    def run(self):
        self.start_output_thread()
        while self.pyboy.tick():
            if not self.command_queue.empty():
                command = self.command_queue.get()
                if command == "EXIT":
                    break
                self.pyboy.button(command)

        self.pyboy.stop()

    def command(self, command):
        if command == "EXIT":
            self.command_queue.put("EXIT")
            return

        if command in key_map:
            button = key_map[command]
            self.command_queue.put(button)
    
    def start_output_thread(self):
        self.output_thread = threading.Thread(target=self.capture_image, daemon=True)
        self.output_thread.start()

    def capture_image(self):
        while True:
            if self.output_queue.empty():
                with self.image_lock: 
                    self.image = self.pyboy.screen.image.copy()
                self.output_queue.put((self.image, self.pyboy.game_wrapper.game_area_collision()))    
            

    def get_output(self):
        return self.image, self.pyboy.game_wrapper.game_area_collision()

if __name__ == "__main__":
    gamefile = read_config("Settings", "gamefile", default="emulation/game.gb")
    game = GameInstance(gamefile)
    game_service = GameService(game.command_queue, game.output_queue)
    threading.Thread(target=game_service.start_game, daemon=True).start()
    game.run()
