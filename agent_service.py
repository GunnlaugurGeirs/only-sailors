import base64
import io
import torch
import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from PIL import Image
from transformers import pipeline

# TODO: check CUDA requirements and throw error if CUDA is not available

# Define the pre-prompt (system instruction) that the LLM should always see first.
PRE_PROMPT = "You are a helpful assistant that is aware of previous conversation context. Please use the context to provide thorough answers."


# Initialize FastAPI
app = FastAPI(title="Conversational Gemma-3-4B-IT Pipeline Service")

class ChatPayload(BaseModel):
    text: str
    image: Optional[str] = None  # Base64-encoded image

model_name = "google/gemma-3-4b-it"
llm_pipeline = pipeline(
    "image-text-to-text",
    model=model_name,
    device="cuda",
    torch_dtype=torch.bfloat16
)

@app.post("/chat")
async def chat(payload: ChatPayload):
    conversation_history: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": [{"type": "text", "text": PRE_PROMPT}]
        }
    ]

    # If an image is provided, decode it. In this example we only include a placeholder.
    image_content = None
    if payload.image:
        try:
            image_data = base64.b64decode(payload.image)
            img = Image.open(io.BytesIO(image_data)).convert("RGB")
            # TODO: handle images. This is just a placeholder
            image_content = {"type": "image", "url": "pixel.png"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image data: {e}")

    # Create a new user message. If there's an image, include it along with the text.
    user_message_content = []
    if image_content:
        user_message_content.append(image_content)
    # Append the text part.
    user_message_content.append({"type": "text", "text": payload.text})

    # Append this user message to the conversation history.
    conversation_history.append({
        "role": "user",
        "content": user_message_content
    })

    try:
        # Call the LLM pipeline with the entire conversation history.
        output = llm_pipeline(text=conversation_history, max_new_tokens=2000)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Inference failed: {e}")

    # Clean up model response and reply
    assistant_response = output[0].get("generated_text", "")
    assistant_message = {
        "role": "assistant",
        "content": [{"type": "text", "text": assistant_response}]
    }
    conversation_history.append(assistant_message)

    return {"response": assistant_response, "conversation_history": conversation_history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
