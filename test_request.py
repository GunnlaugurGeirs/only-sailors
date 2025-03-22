import requests
import base64

# Use the /chat endpoint instead of /predict
url = "http://localhost:8000/chat"

# Example prompt text
prompt = "I have two apples. My friend Timmy has 9 apples. He gives his apples to me. My friend Rich then gives me four more apples. How many apples do I have?"

# If you want to send an image, uncomment and adjust the following:
with open("pixel.png", "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode("utf-8")

payload = {
    "text": prompt,
    "image": image_data
}

response = requests.post(url, json=payload)

if response.ok:
    print("Response from server:", response.json()['response'][-1])
else:
    print("Request failed with status code:", response.status_code)
    print("Error message:", response.text)
