import time
import requests
import base64
import json
import re
import random

from queue import Queue
from constants import key_map
from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO
from typing import Tuple


class GameService(ABC):
    def __init__(self, command_queue: Queue, output_queue: Queue):
        self.command_queue = command_queue
        self.data_queue = output_queue
        self._time_last_command = 0

    def start_game(self):
        while True:
            self.run_agent()

    @abstractmethod
    def parse_command(self, output):
        raise NotImplementedError("Method not implemented")

    @abstractmethod
    def run_agent(self):
        raise NotImplementedError("Method not implemented")


class HTTPGameService(GameService):
    def __init__(self, command_queue: Queue, output_queue: Queue, url: str = "http://localhost:8000/chat"):
        self.url = url
        super().__init__(command_queue, output_queue)

    def _encode_pil_image(self, pil_image: Image):
        """Encode PIL Image to base64 string"""
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def stream_chat_request(
            self,
            prompt: str, 
            image: Image = None,
    ) -> str:
        # Prepare request payload
        payload = {"prompt": prompt}
        
        # Handle optional image
        if image is not None:
            payload['image'] = self._encode_pil_image(image)
        
        # Send request
        response = requests.post(self.url, json=payload, stream=True)
        response.raise_for_status()
            
        # Collect response
        full_response = ""
        for line in response.iter_lines():
            if line:
                try:
                    # Decode and parse JSON
                    decoded_line = line.decode('utf-8')
                    json_response = json.loads(decoded_line)
                    
                    # Extract and print response
                    chunk = json_response.get('response', '')
                    print(chunk, end='', flush=True)
                    full_response += chunk
                except json.JSONDecodeError:
                    print(f"Error decoding line: {line}")
        
        print()  # New line after response
        return full_response

    def parse_command(self, model_output: str) -> Tuple:
        # Regex pattern to match function name and argument
        pattern = r'(\w+)\(["\']([^"\']+)["\']\)'
        matches = list(re.finditer(pattern, model_output))
        
        if not matches:
            raise ValueError(f"Could not find a function call in {model_output}")

        return (matches[-1].group(1), matches[-1].group(2))

    def run_agent(self):
        if self._time_last_command > time.time() - 5:
            return
        image, collision = self.data_queue.get()
        prompt = "This is an image of your current screen. Compare and contrast it to your current screen and previous command, if any. Has your command had any effect on the game state? After you have compared and contrasted your current screen to your previous command, give a short description of what you see and what your current goal is. Then, decide what you want to do next."
        response = self.stream_chat_request(prompt, image)
        try:
            command = self.parse_command(response)[1]
            self.command_queue.put(command)
        except KeyError:
            # TODO: we should inform the LLM when it does an oopsie
            print("INVALID INPUT", command)
        self._time_last_command = time.time()


class MockGameService(GameService):
    def parse_command(self, output):
        return random.choice(list(key_map))

    def run_agent(self):
        image, collision = self.data_queue.get()
        time.sleep(5) # Simulate the agent being slow
        key = self.parse_command(None)
        print(f"Key: {key}")
        self.command_queue.put(key)
        time.sleep(2)
