from queue import Queue
import time
import threading
from constants import key_map, get_random_key
from abc import ABC, abstractmethod


class GameService(ABC):
    def __init__(self, command_queue: Queue, output_queue: Queue):
        self.command_queue = command_queue
        self.output_queue = output_queue

    def start_game(self):
        threading.Thread(target=self.read_input, daemon=True).start()
        threading.Thread(target=self.process_output, daemon=True).start()

    @abstractmethod
    def read_input(self):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def process_output(self):
        raise NotImplementedError("Method not implemented")


class HTTPGameService(GameService):
    def __init__(self, command_queue: Queue, output_queue: Queue):
        super().__init__(command_queue, output_queue)

    def read_input(self):
        raise NotImplementedError("Method not implemented")

    def process_output(self):
        raise NotImplementedError("Method not implemented")


class MockGameService(GameService):
    def __init__(self, command_queue: Queue, output_queue: Queue):
        super().__init__(command_queue, output_queue)

    def read_input(self):
        """Simulate random key inputs for mock purposes."""
        while True:
            if not self.command_queue.full():
                key = get_random_key(key_map)
                self.command_queue.put(key)
                time.sleep(2)

    def process_output(self):
        """Simulate game output."""
        while True:
            if not self.output_queue.empty():
                image, collision = self.output_queue.get()
                print("Collision: ", collision)
                print("Image: ", image)
                time.sleep(5)
