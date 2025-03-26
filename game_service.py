from queue import Queue
import time
import threading
import requests
import base64
import json
from constants import key_map, get_random_key
from abc import ABC, abstractmethod
from PIL import Image
from io import BytesIO
import re


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

    def encode_pil_image(self, pil_image: Image):
        """Encode PIL Image to base64 string"""
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def stream_chat_request(
            self,
            prompt: str, 
            image: Image = None, 
            url: str = "http://localhost:8000/chat"
    ) -> str:
        """
        Stream chat request to the Gemma service
        
        Args:
            prompt (str): Text prompt to send
            image_path (Optional[str]): Path to image file
            url (str): Endpoint URL
        
        Returns:
            str: Full response from the service
        """
        # Prepare request payload
        payload = {"prompt": prompt}
        
        # Handle optional image
        if image is not None:
            payload['image'] = self.encode_pil_image(image)
        
        # Send request
        response = requests.post(url, json=payload, stream=True)
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

    def parse_command(self, model_output):
        """
        Parse the last occurrence of input function name and argument.
        
        Args:
            model_output (str): The text output from the model
        
        Returns:
            tuple or None: (function_name, argument), or None if no match found
        """
        
        # Regex pattern to match function name and argument
        pattern = r'(\w+)\(["\']([^"\']+)["\']\)'
        
        matches = list(re.finditer(pattern, model_output))
        
        return (matches[-1].group(1), matches[-1].group(2)) if matches else None

    def simulate_agent(self):
        while True:
            image, collision = self.output_queue.get()
            prompt = "This is an image of your current screen. Give a short description of what you see and what your current goal is. Then, decide what you want to do next."
            response = self.stream_chat_request(prompt, image)
            try:
                command = self.parse_command(response)[1]
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
