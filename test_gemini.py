import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
model = os.environ.get("GEMMA_MODEL", "gemini-2.5-flash") # Fallback to standard model name for test

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

headers = {
    'Content-Type': 'application/json',
}

data = {
    "contents": [{
        "parts": [{"text": "Say OK"}]
    }]
}

req = urllib.request.Request(
    url, 
    data=json.dumps(data).encode('utf-8'), 
    headers=headers, 
    method='POST'
)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("SUCCESS Reply:", result['candidates'][0]['content']['parts'][0]['text'])
except Exception as e:
    print("REST FAILED:", type(e).__name__, e)