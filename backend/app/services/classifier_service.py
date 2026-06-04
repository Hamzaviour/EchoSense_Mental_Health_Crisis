"""Mental health zero-shot classifier using transformers pipeline."""

_classifier = None
LABELS = [
    "Depression",
    "Anxiety",
    "Stress",
    "Self-Harm",
    "Suicidal Ideation",
    "Normal",
]


def _get_classifier():
    global _classifier
    if _classifier is None:
        from transformers import pipeline

        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1,
        )
    return _classifier


def classify_mental_health(text: str, enabled: bool = True) -> dict:
    if not enabled or not text.strip():
        return {"label": "Normal", "score": 0.0, "component_score": 0.0}
    try:
        clf = _get_classifier()
        result = clf(text[:512], candidate_labels=LABELS, multi_label=True)
        labels = result["labels"]
        scores = result["scores"]
        top_label = labels[0]
        top_score = scores[0]
        risk_labels = {"Self-Harm", "Suicidal Ideation", "Depression", "Anxiety", "Stress"}
        component = 0.0
        for label, score in zip(labels, scores):
            if label in risk_labels:
                weight = 1.0 if label in ("Self-Harm", "Suicidal Ideation") else 0.7
                component = max(component, score * 100 * weight)
        return {
            "label": top_label,
            "score": top_score,
            "component_score": min(100.0, component),
            "all_scores": dict(zip(labels, scores)),
        }
    except Exception:
        return {"label": "Normal", "score": 0.0, "component_score": 0.0}
