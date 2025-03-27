from abc import ABC, abstractmethod
from typing import Optional
import base64
import ollama
from fastapi import HTTPException
import json
import os

from conversation_memory import ConversationMemory

class LLMAgent(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, image_data: Optional[bytes] = None):
        pass

class GemmaAgent(LLMAgent):
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