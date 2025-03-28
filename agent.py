from typing import Optional
import base64
import ollama
from fastapi import HTTPException
import json
import os

from conversation_memory import ConversationMemory

class LLMAgent:
    def __init__(self, 
                 model: str, 
                 context_size: int = 2048,
                 pre_prompt_path: Optional[str] = None,
                 image_model: Optional[str] = None):
        self.model = model
        self.image_model = image_model
        self.context_size = context_size

        # Read pre-prompt from file if path is provided
        pre_prompt = None
        if pre_prompt_path and os.path.exists(pre_prompt_path):
            with open(pre_prompt_path, 'r') as f:
                pre_prompt = f.read().strip()
        elif pre_prompt_path:
            raise FileNotFoundError(f"Pre-prompt file not found at {pre_prompt_path}")
        
        self.memory = ConversationMemory(
            max_tokens=context_size, 
            pre_prompt=pre_prompt
        )
    
    def generate_response(self, prompt: str, image_data: Optional[bytes] = None):
        try:
            # If an image model is provided, use it to process image data
            # TODO: image_prompt and image_model num_ctx should be configurable
            if image_data and self.image_model:
                image_prompt = 'Describe the image'
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                image_to_text_response = ollama.chat(
                    model=self.image_model, 
                    messages=[{'role': 'user', 'content': image_prompt, 'images': [image_data]}],
                    #options={'num_ctx': self.context_size,}
                )

                prompt += " " + image_to_text_response['message']['content']

            messages = self.memory.get_context() + [{'role': 'user', 'content': prompt}]
            
            if image_data and not self.image_model:
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
