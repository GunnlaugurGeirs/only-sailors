import requests
import base64
# Use the /chat endpoint instead of /predict
url = "http://localhost:8000/chat"

# Example prompt text
prompt = "What does this image contain?"

# URL of the image to be fetched
# Cat
#image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Cat_August_2010-4.jpg/960px-Cat_August_2010-4.jpg"

# Pokemon red screenshot
image_url = "https://cdn.mobygames.com/screenshots/15748095-pokemon-red-version-game-boy-danger-ahead-fat-boy.png"

# Fetch the image from the URL and encode it in base64
response = requests.get(image_url)
if response.ok:
    image_data = base64.b64encode(response.content).decode("utf-8")
else:
    print(f"Failed to download image: {response.status_code}")
    exit(1)

payload = {
    "text": prompt,
    "image": image_data
}

response = requests.post(url, json=payload)

if response.ok:
    print("Response from server:", response.json())
else:
    print("Request failed with status code:", response.status_code)
    print("Error message:", response.text)
