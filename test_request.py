import requests
import base64
import json

def stream_chat_request(
    prompt: str, 
    image_path: str = None, 
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
    if image_path:
        with open(image_path, 'rb') as image_file:
            image_bytes = image_file.read()
            payload['image'] = base64.b64encode(image_bytes).decode('utf-8')
    
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

def main():
    """
    Example usage of streaming chat request
    """
    # Example prompts
    prompts = [
        "Explain quantum computing in simple terms",
        "Can you summarize our last conversation, but on the level of a 6-year old?"
    ]
    
    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        print("Response: ", end='', flush=True)
        
        # Get streamed response
        full_response = stream_chat_request(prompt)
        print("\n\nFull Response:", full_response)

# Run the main function
if __name__ == "__main__":
    main()