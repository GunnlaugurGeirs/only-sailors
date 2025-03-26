import base64
from abc import ABC, abstractmethod
from typing import Optional, List
import uvicorn
import threading
import sys
import select
import tty
import termios
import signal
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import ollama
import json
import os

class ConversationMemory:
    def __init__(self, max_tokens: int = 2048, token_multiplier: int = 4, pre_prompt: Optional[str] = None):
        self.max_tokens = max_tokens
        self.token_multiplier = token_multiplier
        self.pre_prompt = pre_prompt
        self.memory: List[dict] = []
        
        if pre_prompt:
            self.memory.append({'role': 'system', 'content': pre_prompt})
    
    def add_exchange(self, user_prompt: str, model_response: str):
        self.memory.append({'role': 'user', 'content': user_prompt})
        self.memory.append({'role': 'assistant', 'content': model_response})
        self._trim_memory()
    
    def _trim_memory(self):
        while self._calculate_memory_size() > self.max_tokens:
            if len(self.memory) > 1 and self.memory[0]['role'] == 'system':
                if len(self.memory) >= 3:
                    self.memory.pop(1)
                    self.memory.pop(1)
                else:
                    break
            else:
                if len(self.memory) >= 2:
                    self.memory.pop(0)
                    self.memory.pop(0)
                else:
                    break
    
    def _calculate_memory_size(self) -> int:
        total_chars = sum(len(msg['content']) for msg in self.memory)
        return total_chars // self.token_multiplier
    
    def clear(self):
        self.memory = []
        if self.pre_prompt:
            self.memory.append({'role': 'system', 'content': self.pre_prompt})
        print("Memory cleared!")
    
    def get_context(self) -> List[dict]:
        return self.memory
    
    def __str__(self) -> str:
        """
        Create a formatted string representation of the conversation memory
        """
        if not self.memory:
            return "Memory is empty."
        
        formatted_memory = "Conversation Memory:\n"
        formatted_memory += "=" * 50 + "\n"
        
        for i, message in enumerate(self.memory, 1):
            role = message['role'].upper()
            formatted_memory += f"{i}. [{role}]: {message['content']}\n"
            formatted_memory += "-" * 50 + "\n"
        
        formatted_memory += f"\nTotal Messages: {len(self.memory)}\n"
        formatted_memory += f"Estimated Token Count: {self._calculate_memory_size()}"
        
        return formatted_memory

class LLMService(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, image_data: Optional[bytes] = None):
        pass

class GemmaService(LLMService):
    def __init__(self, 
                 model: str = 'gemma3:4b', 
                 context_size: int = 2048,
                 pre_prompt_path: Optional[str] = None):
        self.model = model
        self.context_size = context_size
        
        # Read pre-prompt from file if path is provided
        pre_prompt = None
        if pre_prompt_path and os.path.exists(pre_prompt_path):
            with open(pre_prompt_path, 'r') as f:
                pre_prompt = f.read().strip()
        
        self.memory = ConversationMemory(
            max_tokens=context_size, 
            pre_prompt=pre_prompt
        )
    
    def generate_response(self, prompt: str, image_data: Optional[bytes] = None):
        try:
            messages = self.memory.get_context() + [{'role': 'user', 'content': prompt}]
            
            if image_data:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                messages[-1]['images'] = [image_base64]
            
            def generate():
                full_response = ""
                for chunk in ollama.chat(
                    model=self.model, 
                    messages=messages,
                    stream=True,
                    options={'num_ctx': self.context_size}
                ):
                    if chunk.get('message', {}).get('content'):
                        response_chunk = chunk['message']['content']
                        full_response += response_chunk
                        yield json.dumps({"response": response_chunk}) + "\n"
                
                self.memory.add_exchange(prompt, full_response)
            
            return generate()
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

class ChatRequest(BaseModel):
    prompt: str
    image: Optional[str] = None

app = FastAPI()

# Use pre-prompt from file in the same directory
pre_prompt_path = os.path.join(os.path.dirname(__file__), 'preprompt.txt')
llm_service = GemmaService(pre_prompt_path=pre_prompt_path, context_size=32768)

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        image_data = base64.b64decode(request.image) if request.image else None
        
        return StreamingResponse(
            llm_service.generate_response(
                prompt=request.prompt, 
                image_data=image_data
            ), 
            media_type="text/event-stream"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])

# Global variable to store original terminal settings
original_terminal_settings = None

def save_terminal_settings():
    global original_terminal_settings
    original_terminal_settings = termios.tcgetattr(sys.stdin)

def restore_terminal_settings(signum=None, frame=None):
    global original_terminal_settings
    if original_terminal_settings:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, original_terminal_settings)
    sys.exit(0)

def keyboard_handler():
    try:
        tty.setcbreak(sys.stdin.fileno())
        while True:
            if is_data():
                c = sys.stdin.read(1)
                if c == 'c':
                    llm_service.memory.clear()
                elif c == 'p':
                    print(str(llm_service.memory))
    finally:
        restore_terminal_settings()

def start_keyboard_thread():
    keyboard_thread = threading.Thread(target=keyboard_handler, daemon=True)
    keyboard_thread.start()

if __name__ == "__main__":
    # Save original terminal settings before modifying
    save_terminal_settings()
    
    # Register signal handlers to restore terminal settings
    signal.signal(signal.SIGINT, restore_terminal_settings)
    signal.signal(signal.SIGTERM, restore_terminal_settings)
    
    start_keyboard_thread()
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000
    )