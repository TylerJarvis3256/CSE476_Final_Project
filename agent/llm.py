import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

# API key
API_KEY = os.environ["OPENAI_API_KEY"]
API_BASE = os.environ["API_BASE"]
MODEL_NAME = os.environ["MODEL_NAME"]

# Call usage
CALL_CAP_PER_ITEM = 15
CALL_WARN_AT = 12

class CallBudgetExceeded(Exception):
    pass

# Private Globals
_call_count = 0

def get_call_count():
    return _call_count

def reset_call_count():
    global _call_count
    _call_count = 0

REQUEST_TIMEOUT_S = 60

# The good stuff
def call_model(messages, temperature=0.0, max_tokens=512, stop=None) -> str:
    global _call_count

    if _call_count >= CALL_CAP_PER_ITEM:
        raise CallBudgetExceeded(f"hit per-item cap of {CALL_CAP_PER_ITEM}")
    
    if _call_count >= CALL_WARN_AT:
        print(f"[warn] near call cap: {_call_count}/{CALL_CAP_PER_ITEM}")
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type":"application/json"}
    payload = {"model": MODEL_NAME, "messages": messages, "temperature":temperature, "max_tokens": max_tokens}

    if stop is not None:
        payload["stop"] = stop
    
    url = f"{API_BASE}/chat/completions"
    last_error = None

    for attempt in range(3):
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_S)
        except requests.exceptions.ConnectionError as e:
            last_error = e
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            continue
        if response.status_code >= 500:
            last_error = RuntimeError(f"server error {response.status_code}:{response.text[:200]}")
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"API error {response.status_code}:{response.text[:500]}")
        _call_count += 1
        return response.json()["choices"][0]["message"]["content"]
    raise last_error if last_error else RuntimeError("all retries exhausted with no error captured")

if __name__ == "__main__":
    messages = [{"role": "user", "content": "Say hi in exactly 3 words"}]
    print(call_model(messages))
    print(f"calls: {get_call_count()}")