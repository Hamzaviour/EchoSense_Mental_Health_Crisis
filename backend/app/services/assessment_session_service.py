from datetime import datetime

from app.extensions import db
from app.models import Assessment, Gad7Result, Phq9Result, Who5Result
from app.models.assessment_session import AssessmentAnswer, AssessmentScore, AssessmentSession, SessionStatus

TYPE_LABELS = {"PHQ9": "PHQ-9", "GAD7": "GAD-7", "WHO5": "WHO-5"}
TYPE_MAX = {"PHQ9": 27, "GAD7": 21, "WHO5": 25}
TYPE_QUESTION_COUNT = {"PHQ9": 9, "GAD7": 7, "WHO5": 5}


def _total_questions(types: list[str]) -> int:
    return sum(TYPE_QUESTION_COUNT.get(t, 0) for t in types)


def _questions_for_type(atype: str):
    return (
        Assessment.query.filter_by(assessment_type=atype)
        .order_by(Assessment.question_number.asc())
        .all()
    )


def get_active_session(patient_id: int) -> AssessmentSession | None:
    return (
        AssessmentSession.query.filter_by(patient_id=patient_id)
        .filter(AssessmentSession.status.in_([
            SessionStatus.OFFERED,
            SessionStatus.ACCEPTED,
            SessionStatus.IN_PROGRESS,
        ]))
        .order_by(AssessmentSession.offered_at.desc())
        .first()
    )


def create_offered_session(patient_id: int, types: list[str]) -> AssessmentSession:
    existing = get_active_session(patient_id)
    if existing and existing.status == SessionStatus.OFFERED:
        existing.assessment_types = types
        return existing
    session = AssessmentSession(
        patient_id=patient_id,
        status=SessionStatus.OFFERED,
        assessment_types=types,
        current_type=types[0] if types else None,
        current_question_index=0,
    )
    db.session.add(session)
    db.session.flush()
    return session


def accept_session(session: AssessmentSession) -> AssessmentSession:
    session.status = SessionStatus.IN_PROGRESS
    session.accepted_at = datetime.utcnow()
    session.current_type = session.assessment_types[0]
    session.current_question_index = 1
    _refresh_progress(session)
    return session


def decline_session(session: AssessmentSession):
    session.status = SessionStatus.DECLINED
    db.session.commit()


def _current_question(session: AssessmentSession):
    if not session.current_type:
        return None
    return Assessment.query.filter_by(
        assessment_type=session.current_type,
        question_number=session.current_question_index,
    ).first()


def _advance(session: AssessmentSession):
    count = TYPE_QUESTION_COUNT.get(session.current_type, 0)
    if session.current_question_index < count:
        session.current_question_index += 1
        return
    idx = session.assessment_types.index(session.current_type)
    if idx + 1 < len(session.assessment_types):
        session.current_type = session.assessment_types[idx + 1]
        session.current_question_index = 1
    else:
        session.status = SessionStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        _finalize_all_scores(session)


def _refresh_progress(session: AssessmentSession):
    answered = session.answers.count()
    total = _total_questions(session.assessment_types)
    session.progress_percent = round((answered / total) * 100, 1) if total else 0
    if session.current_type:
        partial = (
            AssessmentAnswer.query.filter_by(
                session_id=session.id, assessment_type=session.current_type
            ).count()
        )
        score_row = AssessmentScore.query.filter_by(
            session_id=session.id, assessment_type=session.current_type
        ).first()
        if not score_row:
            score_row = AssessmentScore(
                session_id=session.id,
                patient_id=session.patient_id,
                assessment_type=session.current_type,
                max_score=TYPE_MAX.get(session.current_type, 0),
            )
            db.session.add(score_row)
        answers = AssessmentAnswer.query.filter_by(
            session_id=session.id, assessment_type=session.current_type
        ).all()
        score_row.partial_score = sum(a.answer_value for a in answers)
        score_row.progress_percent = session.progress_percent


def save_answer(session: AssessmentSession, question_id: int, value: int) -> dict:
    q = Assessment.query.get(question_id)
    if not q:
        raise ValueError("Question not found")

    existing = AssessmentAnswer.query.filter_by(
        session_id=session.id, question_id=question_id
    ).first()
    if existing:
        existing.answer_value = value
        existing.answered_at = datetime.utcnow()
    else:
        db.session.add(
            AssessmentAnswer(
                session_id=session.id,
                patient_id=session.patient_id,
                question_id=question_id,
                question_number=q.question_number,
                assessment_type=q.assessment_type,
                answer_value=value,
            )
        )
        if (
            q.assessment_type == session.current_type
            and q.question_number == session.current_question_index
        ):
            _advance(session)

    _refresh_progress(session)
    db.session.flush()
    return get_session_state(session)


def _phq_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    if score <= 9:
        return "Mild"
    if score <= 14:
        return "Moderate"
    if score <= 19:
        return "Moderately Severe"
    return "Severe"


def _gad_severity(score: int) -> str:
    if score <= 4:
        return "Minimal"
    if score <= 9:
        return "Mild"
    if score <= 14:
        return "Moderate"
    return "Severe"


def _finalize_type(session: AssessmentSession, atype: str):
    answers = AssessmentAnswer.query.filter_by(
        session_id=session.id, assessment_type=atype
    ).order_by(AssessmentAnswer.question_number.asc()).all()
    if not answers:
        return
    total = sum(a.answer_value for a in answers)
    responses = [{"question_number": a.question_number, "value": a.answer_value} for a in answers]

    if atype == "PHQ9":
        sev = _phq_severity(total)
        db.session.add(Phq9Result(
            patient_id=session.patient_id, total_score=total, severity=sev, responses=responses
        ))
        try:
            from app.services.notification_service import notify_phq_completed
            notify_phq_completed(session.patient_id, total, sev)
        except Exception:
            pass
    elif atype == "GAD7":
        sev = _gad_severity(total)
        db.session.add(Gad7Result(
            patient_id=session.patient_id, total_score=total, severity=sev, responses=responses
        ))
    elif atype == "WHO5":
        index = total * 4
        sev = "Good wellbeing" if index >= 50 else "Moderate wellbeing" if index >= 28 else "Poor wellbeing"
        db.session.add(Who5Result(
            patient_id=session.patient_id,
            raw_score=total,
            wellbeing_index=index,
            severity=sev,
            responses=responses,
        ))


def _finalize_all_scores(session: AssessmentSession):
    for atype in session.assessment_types:
        _finalize_type(session, atype)


def get_assessment_context_for_rag(patient_id: int) -> dict:
    session = get_active_session(patient_id)
    if not session or session.status not in (SessionStatus.IN_PROGRESS, SessionStatus.ACCEPTED):
        return {}
    scores = {}
    for s in session.scores:
        scores[s.assessment_type.lower().replace("phq9", "phq9").replace("gad7", "gad7")] = s.partial_score
    phq = AssessmentScore.query.filter_by(session_id=session.id, assessment_type="PHQ9").first()
    return {
        "phq_score": phq.partial_score if phq else 0,
        "assessment_progress": session.progress_percent,
        "current_type": TYPE_LABELS.get(session.current_type, session.current_type),
    }


def get_session_state(session: AssessmentSession) -> dict:
    q = _current_question(session)
    total = _total_questions(session.assessment_types)
    answered = session.answers.count()
    type_idx = session.assessment_types.index(session.current_type) if session.current_type in session.assessment_types else 0
    type_count = len(session.assessment_types)

    current_q = None
    if q and session.status == SessionStatus.IN_PROGRESS:
        prefix = ""
        if session.current_type in ("PHQ9", "GAD7"):
            prefix = "Over the last 2 weeks, how often have you "
        current_q = {
            "id": q.id,
            "number": q.question_number,
            "text": f"{prefix}{q.question_text.rstrip('?')}?",
            "options": q.options,
            "assessment_type": session.current_type,
            "type_label": TYPE_LABELS.get(session.current_type, session.current_type),
        }

    return {
        "session_id": session.id,
        "status": session.status.value,
        "assessment_types": session.assessment_types,
        "type_labels": [TYPE_LABELS.get(t, t) for t in session.assessment_types],
        "current_type": session.current_type,
        "current_type_label": TYPE_LABELS.get(session.current_type or "", ""),
        "current_question_index": session.current_question_index,
        "total_questions": total,
        "answered_count": answered,
        "remaining": max(0, total - answered),
        "progress_percent": session.progress_percent,
        "type_progress": f"Question {session.current_question_index} of {TYPE_QUESTION_COUNT.get(session.current_type, 0)}",
        "form_index": f"Form {type_idx + 1} of {type_count}",
        "current_question": current_q,
        "is_complete": session.status == SessionStatus.COMPLETED,
    }
