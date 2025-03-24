import base64
import io
import torch
import traceback
import copy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from PIL import Image
from transformers import Gemma3ForConditionalGeneration, AutoProcessor

# https://ai.google.dev/gemma/docs/capabilities/function-calling

# Read pre-prompt from file
with open("preprompt.txt", "r") as file:
    PRE_PROMPT = file.read().strip()


class ChatPayload(BaseModel):
    text: str
    image: Optional[str] = None  # Base64-encoded image


model_name = "google/gemma-3-4b-it"
model = Gemma3ForConditionalGeneration.from_pretrained(
    model_name, device_map="cuda", torch_dtype=torch.bfloat16
)
processor = AutoProcessor.from_pretrained(model_name)


class LLMService:
    def __init__(self):
        self.__init_conversation_history()

    def __init_conversation_history(self):
        self.conversation_history: List[Dict[str, Any]] = [
            {"role": "system", "content": [{"type": "text", "text": PRE_PROMPT}]}
        ]

    async def handle_chat(self, payload: ChatPayload):
        self.__init_conversation_history()
        image_content = None
        if payload.image:
            try:
                image_data = base64.b64decode(payload.image)
                img = Image.open(io.BytesIO(image_data))
                image_content = {"type": "image", "image": img}
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

        user_message_content = []
        if image_content:
            user_message_content.append(image_content)
        user_message_content.append({"type": "text", "text": payload.text})

        self.conversation_history.append(
            {"role": "user", "content": user_message_content}
        )

        try:
            inputs = processor.apply_chat_template(
                self.conversation_history,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                do_pan_and_scan=True,
                padding="longest",
                pad_to_multiple_of=8,
            ).to(model.device)

            processor.tokenizer.padding_side = "left"

            input_len = inputs["input_ids"].shape[-1]
            output_ids = model.generate(**inputs, max_new_tokens=2000)
            output_ids = output_ids[0][input_len:]
            assistant_response = processor.decode(
                output_ids, skip_special_tokens=True, return_full_text=False
            )
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

        # TODO: fix conversation history if above code fails
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": assistant_response}],
        }
        self.conversation_history.append(assistant_message)
        return assistant_response


LLM_SERVICE = LLMService()

# Initialize FastAPI
APP = FastAPI(title="Conversational Gemma-3-4B-IT Pipeline Service")


@APP.post("/chat")
async def chat(payload: ChatPayload):
    return await LLM_SERVICE.handle_chat(payload)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
