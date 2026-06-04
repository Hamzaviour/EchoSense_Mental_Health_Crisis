import os

import requests
from flask import current_app


def analyze_sentiment(text: str) -> dict:
    api_key = current_app.config.get("API_NINJAS_API_KEY") or os.getenv("API_NINJAS_API_KEY", "")
    if not api_key:
        return _fallback_sentiment(text)
    try:
        resp = requests.get(
            "https://api.api-ninjas.com/v1/sentiment",
            headers={"X-Api-Key": api_key},
            params={"text": text[:5000]},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and data:
            data = data[0]
        score = float(data.get("score", 0.5))
        sentiment = data.get("sentiment", "neutral")
        return {"score": score, "sentiment": sentiment}
    except Exception:
        return _fallback_sentiment(text)


def _fallback_sentiment(text: str) -> dict:
    negative_words = ["sad", "hopeless", "anxious", "depressed", "die", "hurt", "afraid", "alone"]
    lower = text.lower()
    hits = sum(1 for w in negative_words if w in lower)
    if hits >= 3:
        return {"score": 0.85, "sentiment": "negative"}
    if hits >= 1:
        return {"score": 0.55, "sentiment": "neutral"}
    return {"score": 0.3, "sentiment": "positive"}
