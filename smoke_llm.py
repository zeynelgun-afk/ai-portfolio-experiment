import urllib.request
import json
import os

key = os.environ.get("OPENROUTER_API_KEY")
req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    data=json.dumps({
        "model": "google/gemini-flash-1.5-8b",
        "messages": [{"role": "user", "content": "Hello, answer YES or NO: is the sky blue?"}]
    }).encode("utf-8")
)
try:
    with urllib.request.urlopen(req) as response:
        print(json.loads(response.read().decode("utf-8"))["choices"][0]["message"]["content"])
except Exception as e:
    print(e)
