"""Select PHQ-9, GAD-7, or WHO-5 based on conversation signals."""

DEPRESSION_SIGNALS = [
    "hopeless", "depressed", "sad", "exhausted", "tired", "empty", "worthless",
    "no energy", "can't sleep", "insomnia", "no interest", "nothing matters",
]

ANXIETY_SIGNALS = [
    "anxious", "anxiety", "worried", "panic", "nervous", "on edge", "overwhelmed",
    "racing thoughts", "can't stop thinking", "restless", "tense", "afraid",
]

WELLBEING_SIGNALS = [
    "wellbeing", "well-being", "quality of life", "cheerful", "not myself lately",
]


def is_crisis_message(text: str, keyword_result: dict) -> bool:
    return bool(keyword_result.get("suicide_flag"))


def recommend_assessment_types(text: str, risk_score: float) -> list[str]:
    lower = text.lower()
    dep = sum(1 for s in DEPRESSION_SIGNALS if s in lower)
    anx = sum(1 for s in ANXIETY_SIGNALS if s in lower)
    well = sum(1 for s in WELLBEING_SIGNALS if s in lower)

    if dep >= 1 and anx >= 1:
        return ["PHQ9", "GAD7"]
    if dep >= 1 or risk_score >= 31:
        return ["PHQ9"]
    if anx >= 1:
        return ["GAD7"]
    if well >= 1 or risk_score < 31:
        return ["WHO5"]
    return ["PHQ9"]


def assessment_offer_message(first_name: str) -> str:
    return (
        f"Thank you for sharing that, {first_name}. To better understand how these feelings "
        "have been affecting you, I'd like to ask a few brief questions that are commonly used "
        "by mental health professionals. It usually takes less than two minutes. Would that be okay?"
    )
