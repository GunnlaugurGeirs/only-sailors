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
        #threading.Thread(target=self.simulate_input, daemon=True).start()
        #threading.Thread(target=self.simulate_output, daemon=True).start()
        threading.Thread(target=self.simulate_agent, daemon=True).start()

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
        command = output[closing_index + len(closing_tag):].strip()
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
                "image": image_data
            }
            response = requests.post("http://localhost:8000/chat", json=payload)
            # TODO: parse response
            print(response.json())
            try:
                command = self.parse_command(response.json())
                self.command_queue.put(key_map[command])
            except KeyError:
                print("INVALID INPUT", command)
            #time.sleep(5)