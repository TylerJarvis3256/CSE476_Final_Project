import os
import time
import requests
from dotenv import load_dotenv

#load values from a local .env file, this is how people don't leak the API keys apparently
load_dotenv()

#read that API key that should come from the env file
API_KEY = os.getenv("OPENAI_API_KEY")

#default values, not needed from env
API_BASE = "https://openai.rc.asu.edu/v1"
MODEL_NAME = "qwen3-30b-a3b-instruct-2507"

#total count across logic
call_count = 0
#return the current call count to ensure success
def get_call_count():
    return call_count

def reset_call_count():
    #reset the count before a new item gets processed
    global call_count
    call_count = 0

def build_messages(user_prompt, system_prompt=None):
    #build the chat message list
    if system_prompt is None:
        system_prompt = "You are a helpful assistant."
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

def call_model(messages, temperature=0.0, max_tokens=512):
    #send one request to the ASU LLM API and return the text response
    global call_count

    if not API_KEY:
        print("Missing OPENAI_API_KEY in .env")
        return None

    if call_count >= 15:
        print("COUNT EXCEEDED: Hit per item cap")
        return None

    if call_count >= 12:
        print("Warning: near call cap:", call_count/15)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


    #retry a few times if there is a temporary network or server problem.
    for i in range(3):
        response = requests.post(f"{API_BASE}/chat/completions", json=payload, headers=headers, timeout=60)
        if response.status_code >= 500:
            print("server error",response.status_code,response.text)
            time.sleep(3)
            continue
        if response.status_code >= 400:
            print("API error", response.status_code, " : ",response.text)
            time.sleep(3)
            continue
        data = response.json()
        call_count += 1
        return data["choices"][0]["message"]["content"]

    print("Model call failed after retries")
    return None


if __name__ == "__main__":
    sample_messages = build_messages("Say hi in exactly three words.")
    print(call_model(sample_messages))
    print(f"calls: {get_call_count()}")
