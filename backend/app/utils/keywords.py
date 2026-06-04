SUICIDE_KEYWORDS = [
    "kill myself", "end my life", "want to die", "suicide", "suicidal",
    "no reason to live", "better off dead", "end it all", "take my life",
]

SELF_HARM_KEYWORDS = [
    "hurt myself", "cut myself", "self harm", "self-harm", "burn myself",
    "harm myself", "injure myself",
]

DEPRESSION_KEYWORDS = [
    "hopeless", "worthless", "empty inside", "can't get out of bed",
    "no energy", "nothing matters", "depressed", "sad all the time",
    "don't care anymore", "numb",
]

ANXIETY_KEYWORDS = [
    "panic attack", "can't breathe", "racing heart", "anxious", "worried",
    "on edge", "overwhelmed", "can't stop thinking", "restless", "tense",
]

CRISIS_KEYWORDS = SUICIDE_KEYWORDS + SELF_HARM_KEYWORDS


def keyword_score(text: str) -> dict:
    lower = text.lower()
    suicide = sum(1 for k in SUICIDE_KEYWORDS if k in lower)
    self_harm = sum(1 for k in SELF_HARM_KEYWORDS if k in lower)
    depression = sum(1 for k in DEPRESSION_KEYWORDS if k in lower)
    anxiety = sum(1 for k in ANXIETY_KEYWORDS if k in lower)
    total = suicide + self_harm + depression + anxiety
    score = min(100.0, total * 15.0)
    return {
        "score": score,
        "suicide_hits": suicide,
        "self_harm_hits": self_harm,
        "depression_hits": depression,
        "anxiety_hits": anxiety,
        "suicide_flag": suicide > 0 or self_harm > 0,
    }
