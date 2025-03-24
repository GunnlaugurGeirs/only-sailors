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
        threading.Thread(target=self.process_output, daemon=True).start()
        threading.Thread(target=self.read_input, daemon=True).start()
        threading.Thread(target=self.simulate_agent, daemon=True).start()

    @abstractmethod
    def read_input(self):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def process_output(self):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def parse_command(self, output):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def simulate_agent(self):
        raise NotImplementedError("Method not implemented")


class HTTPGameService(GameService):
    def __init__(self, command_queue: Queue, output_queue: Queue):
        super().__init__(command_queue, output_queue)

    def read_input(self):
        return

    def process_output(self):
        return

    def parse_command(self, output):
        """
        Parses the command from the given output string.
        The expected format is:
        <think>...internal reasoning...</think>COMMAND
        where COMMAND is one of the key_map commands.
        """
        # Find the closing </think> tag
        closing_tag = "</think>"
        closing_index = output.find(closing_tag)
        if closing_index == -1:
            raise ValueError("No closing </think> tag found in the output.")

        # The command is everything after the closing tag
        command = output[closing_index + len(closing_tag) :].strip()
        return command

    def simulate_agent(self):
        import base64, requests
        from io import BytesIO

        while True:
            image, collision = self.output_queue.get()
            # Assuming 'image' is your PIL Image object
            buffered = BytesIO()
            image.save(buffered, format="PNG")  # You can change the format if needed
            image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            payload = {
                "text": "Here's an image of the current screen. Repeat out loud what your instructions are, then what you see in great detail, then decide what you want to do next. Make sure to follow your instructions, include your thought process in <think>!",
                "image": image_data,
            }
            response = requests.post("http://localhost:8000/chat", json=payload)
            # TODO: parse response
            print(response.json())
            try:
                command = self.parse_command(response.json())
                self.command_queue.put(key_map[command])
            except KeyError:
                print("INVALID INPUT", command)
            # time.sleep(5)


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
                time.sleep(5)

    def parse_command(self, output):
        raise NotImplementedError("Method not implemented")

    def simulate_agent(self):
        return
