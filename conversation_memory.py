from typing import Optional, List

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