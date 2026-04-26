import os
import time

import requests
from dotenv import load_dotenv

# Load values from a local .env file if one exists.
load_dotenv()

# Read the ASU API settings from environment variables.
API_KEY = os.getenv("OPENAI_API_KEY", "sk-tRX7eS_JfCfGCfC6-1xvKg")
API_BASE = os.getenv("API_BASE", "https://openai.rc.asu.edu/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-30b-a3b-instruct-2507")

# The assignment wants low call usage, so I track calls for each question.
CALL_CAP_PER_ITEM = 15
CALL_WARN_AT = 12
REQUEST_TIMEOUT_S = 60


class CallBudgetExceeded(Exception):
    pass


_call_count = 0


def get_call_count():
    return _call_count


def reset_call_count():
    global _call_count
    _call_count = 0


def build_messages(user_prompt, system_prompt=None):
    # This matches the OpenAI-style chat format expected by the ASU endpoint.
    if system_prompt is None:
        system_prompt = "You are a careful reasoning agent. Follow the output format exactly."

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def call_model(messages, temperature=0.0, max_tokens=512, stop=None):
    global _call_count

    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is missing. Put it in your .env file.")

    if _call_count >= CALL_CAP_PER_ITEM:
        raise CallBudgetExceeded(f"hit per-item cap of {CALL_CAP_PER_ITEM}")

    if _call_count >= CALL_WARN_AT:
        print(f"[warn] near call cap: {_call_count}/{CALL_CAP_PER_ITEM}")

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
    if stop is not None:
        payload["stop"] = stop

    url = f"{API_BASE}/chat/completions"
    last_error = None

    # Retry a few times if the connection fails or the server has a 5xx error.
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=REQUEST_TIMEOUT_S,
            )
        except requests.exceptions.ConnectionError as error:
            last_error = error
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            continue

        if response.status_code >= 500:
            last_error = RuntimeError(
                f"server error {response.status_code}: {response.text[:300]}"
            )
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
            continue

        # Do not retry 4xx errors because those usually mean the request itself is bad.
        if response.status_code >= 400:
            raise RuntimeError(f"API error {response.status_code}: {response.text[:500]}")

        data = response.json()
        _call_count += 1
        return data["choices"][0]["message"]["content"]

    if last_error is not None:
        raise last_error
    raise RuntimeError("the model call failed but no clear error was captured")


if __name__ == "__main__":
    demo_messages = build_messages("What is 17 + 28? Reply with only the number.")
    print(call_model(demo_messages))
    print(f"calls: {get_call_count()}")
