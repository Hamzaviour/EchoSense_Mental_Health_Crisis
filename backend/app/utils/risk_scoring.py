def risk_level_from_score(score: float) -> str:
    if score >= 81:
        return "Critical"
    if score >= 61:
        return "High"
    if score >= 31:
        return "Moderate"
    return "Low"


def sentiment_to_component(score: float, label: str) -> float:
    if label == "negative":
        return min(100.0, score * 100)
    if label == "neutral":
        return 40.0
    return max(0.0, 30.0 - score * 30)


def assessment_component(phq: int | None, gad: int | None, who5_raw: int | None) -> float:
    parts = []
    if phq is not None:
        parts.append(min(100.0, (phq / 27) * 100))
    if gad is not None:
        parts.append(min(100.0, (gad / 21) * 100))
    if who5_raw is not None:
        parts.append(max(0.0, 100 - (who5_raw / 25) * 100))
    return sum(parts) / len(parts) if parts else 0.0


def trend_component(recent_sentiments: list[float]) -> float:
    if len(recent_sentiments) < 2:
        return 0.0
    delta = recent_sentiments[-1] - recent_sentiments[0]
    if delta > 0.1:
        return min(100.0, delta * 200)
    return max(0.0, delta * 100)


def compute_ensemble_risk(
    sentiment_score: float,
    sentiment_label: str,
    keyword_result: dict,
    classifier_score: float,
    assessment_score: float,
    trend_score: float,
    suicide_floor: bool = False,
) -> tuple[float, str, dict]:
    weights = {
        "sentiment": 0.15,
        "keywords": 0.25,
        "classifier": 0.25,
        "assessment": 0.20,
        "trend": 0.15,
    }
    sentiment_comp = sentiment_to_component(sentiment_score, sentiment_label)
    keyword_comp = keyword_result.get("score", 0.0)
    breakdown = {
        "sentiment": round(sentiment_comp, 2),
        "keywords": round(keyword_comp, 2),
        "classifier": round(classifier_score, 2),
        "assessment": round(assessment_score, 2),
        "trend": round(trend_score, 2),
        "weights": weights,
        "keyword_details": keyword_result,
    }
    total = (
        sentiment_comp * weights["sentiment"]
        + keyword_comp * weights["keywords"]
        + classifier_score * weights["classifier"]
        + assessment_score * weights["assessment"]
        + trend_score * weights["trend"]
    )
    if suicide_floor or keyword_result.get("suicide_flag"):
        total = max(total, 85.0)
        breakdown["suicide_floor_applied"] = True
    total = min(100.0, max(0.0, total))
    return total, risk_level_from_score(total), breakdown
