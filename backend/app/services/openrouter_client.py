import os
import time

import openai
from openai import OpenAIError

FREE_MODELS_POOL = [
    "openrouter/free",
    "google/gemma-2-9b-it:free",
    "meta-llama/llama-3-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
]


def _client():
    return openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ.get("OPENROUTER_API_KEY", ""),
    )


def send_chat_completion_with_fallback(messages, max_retries=3, delay=2):
    client = _client()
    for model in FREE_MODELS_POOL:
        retries = 0
        while retries < max_retries:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    extra_headers={
                        "HTTP-Referer": os.getenv("FRONTEND_URL", "http://localhost:5173"),
                        "X-Title": "Echo Sense",
                    },
                )
                return response.choices[0].message.content, getattr(response, "model", model)
            except OpenAIError as e:
                error_code = getattr(e, "status_code", None)
                if error_code in (429, 503, 529):
                    time.sleep(delay * (2**retries))
                    retries += 1
                else:
                    break
    raise RuntimeError("All OpenRouter models failed")


def chat_completion(messages: list[dict]) -> str:
    content, _ = send_chat_completion_with_fallback(messages)
    return content
