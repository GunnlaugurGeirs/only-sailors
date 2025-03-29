import base64
import os
import sys
import select
import tty
import termios
import threading
import signal
import uvicorn
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from agent import LLMAgent
from config import read_config

class ChatRequest(BaseModel):
    prompt: str
    image: Optional[str] = None

class WebService:
    def __init__(self, llm_agent):
        self.app = FastAPI()
        self.llm_agent = llm_agent
        
        # Store original terminal settings
        self.original_terminal_settings = termios.tcgetattr(sys.stdin)
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.post("/chat")
        async def chat_endpoint(request: ChatRequest):
            try:
                image_data = base64.b64decode(request.image) if request.image else None
                
                return StreamingResponse(
                    self.llm_agent.generate_response(
                        prompt=request.prompt, 
                        image_data=image_data
                    ), 
                    media_type="text/event-stream"
                )
            
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

    def restore_terminal_settings(self, *args, **kwargs):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_terminal_settings)
        exit(0)
    
    async def async_keyboard_handler(self):
        loop = asyncio.get_running_loop()
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                # Create a Future that will be set when a key is pressed
                fut = loop.create_future()

                # Register a reader callback to set the future's result when data is available
                loop.add_reader(sys.stdin, lambda: fut.set_result(sys.stdin.read(1)))

                # Wait asynchronously until a key is pressed
                c = await fut

                # Remove the reader to avoid duplicate callbacks
                loop.remove_reader(sys.stdin)

                if c == 'c':
                    # For example, clear memory or perform any other operation
                    self.llm_agent.memory.clear()
                elif c == 'p':
                    print(str(self.llm_agent.memory))
        finally:
            self.restore_terminal_settings()

    def start_keyboard_handler(self):
        threading.Thread(
            target=lambda: asyncio.run(self.async_keyboard_handler()),
            daemon=True
        ).start()
    
    def run(self, host: str, port):
        # Register signal handlers to restore terminal settings
        signal.signal(signal.SIGINT, self.restore_terminal_settings)
        signal.signal(signal.SIGTERM, self.restore_terminal_settings)
        
        # Start keyboard monitoring thread
        self.start_keyboard_handler()
        
        # Run the server
        uvicorn.run(
            self.app, 
            host=host, 
            port=port
        )

def main():
    # TODO: classes here should have builders which read config.

    # Get model name and size from config file
    model = read_config("Agent", "model", default="gemma3:4b", value_type=str)

    # Optional text model, for non multi-modal models that can't handle images.
    image_model = read_config("Agent", "image_model", default=None, value_type=str)

    # Get preprompt filename
    pre_prompt = read_config("Agent", "pre_prompt", default="preprompt.txt", value_type=str)

    # Construct path to preprompt.txt relative to this file
    pre_prompt_path = os.path.join(os.path.dirname(__file__), pre_prompt)

    # Create LLM Agent
    context_size = read_config("Agent", "context_size", default=2048, value_type=int)
    llm_agent = LLMAgent(
        model=model,
        pre_prompt_path=pre_prompt_path,
        context_size=context_size,
        image_model=image_model
    )
    
    # Create and run web service
    host = read_config("Agent", "host", default="0.0.0.0", value_type=str) 
    port = read_config("Agent", "port", default=8000, value_type=int)
    web_service = WebService(llm_agent)
    web_service.run(host=host, port=port)

if __name__ == "__main__":
    main()