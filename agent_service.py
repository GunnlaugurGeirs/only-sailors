import base64
import os
import sys
import select
import tty
import termios
import threading
import signal
import uvicorn

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
        self.original_terminal_settings = None
        
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
    
    def save_terminal_settings(self):
        self.original_terminal_settings = termios.tcgetattr(sys.stdin)
    
    def restore_terminal_settings(self, *args, **kwargs):
        # Otherwise your terminal will break on exit ;^)
        if self.original_terminal_settings:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_terminal_settings)
        sys.exit(0)
    
    def is_data(self):
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
    
    def keyboard_handler(self):
        try:
            tty.setcbreak(sys.stdin.fileno())
            while True:
                if self.is_data():
                    c = sys.stdin.read(1)
                    if c == 'c':
                        self.llm_agent.memory.clear()
                    elif c == 'p':
                        print(str(self.llm_agent.memory))
        finally:
            self.restore_terminal_settings()
    
    def start_keyboard_thread(self):
        keyboard_thread = threading.Thread(target=self.keyboard_handler, daemon=True)
        keyboard_thread.start()
    
    def run(self, host: str, port):
        # Save original terminal settings
        self.save_terminal_settings()
        
        # Register signal handlers to restore terminal settings
        signal.signal(signal.SIGINT, self.restore_terminal_settings)
        signal.signal(signal.SIGTERM, self.restore_terminal_settings)
        
        # Start keyboard monitoring thread
        self.start_keyboard_thread()
        
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