import json
import re

from app.services.openrouter_client import chat_completion
from app.services.sentiment_service import analyze_sentiment


def _parse_ai_json(raw: str) -> dict:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    return {}


def analyze_journal_entry(content: str) -> dict:
    """Return summary, emotions list, and coping strategies for a journal entry."""
    sentiment = analyze_sentiment(content)
    fallback_emotions = [sentiment.get("sentiment", "neutral").title()]

    try:
        raw = chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You analyze private mental health journal entries with empathy. "
                        "Respond ONLY with valid JSON (no markdown): "
                        '{"summary": "2-3 sentence compassionate summary", '
                        '"emotions": ["emotion1", "emotion2"], '
                        '"coping_strategies": ["strategy1", "strategy2", "strategy3"]}. '
                        "Emotions: 2-5 labels. Coping strategies: 3-5 practical, gentle suggestions."
                    ),
                },
                {"role": "user", "content": content[:6000]},
            ]
        )
        parsed = _parse_ai_json(raw)
        summary = (parsed.get("summary") or "").strip()
        emotions = parsed.get("emotions") or []
        strategies = parsed.get("coping_strategies") or parsed.get("strategies") or []
        if not isinstance(emotions, list):
            emotions = [str(emotions)]
        if not isinstance(strategies, list):
            strategies = [str(strategies)]
        emotions = [str(e).strip() for e in emotions if str(e).strip()][:8]
        strategies = [str(s).strip() for s in strategies if str(s).strip()][:8]
        if not summary:
            summary = (
                f"You shared thoughtful reflections. "
                f"Detected tone: {sentiment.get('sentiment', 'neutral')}."
            )
        if not emotions:
            emotions = fallback_emotions
        if not strategies:
            strategies = [
                "Take a few slow breaths when overwhelmed",
                "Reach out to someone you trust",
                "Write one small thing you are grateful for today",
            ]
        return {
            "summary": summary,
            "emotions": emotions,
            "coping_strategies": strategies,
            "sentiment_label": sentiment.get("sentiment"),
            "sentiment_score": sentiment.get("score"),
        }
    except Exception:
        return {
            "summary": (
                "Thank you for taking time to reflect. Your entry has been saved securely. "
                "A counselor can review it if you request support."
            ),
            "emotions": fallback_emotions,
            "coping_strategies": [
                "Practice grounding: name 5 things you can see",
                "Drink water and stretch gently",
                "Consider scheduling a session with a counselor",
            ],
            "sentiment_label": sentiment.get("sentiment"),
            "sentiment_score": sentiment.get("score"),
        }


def journal_entry_to_dict(entry) -> dict:
    return {
        "id": entry.id,
        "entry_type": entry.entry_type.value if entry.entry_type else "TEXT",
        "content": entry.content,
        "transcript": entry.transcript,
        "ai_summary": entry.ai_summary,
        "emotions": entry.emotions or [],
        "coping_strategies": entry.coping_strategies or [],
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
