from datetime import datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import ChatMessage, Patient, SentimentAnalysis, User
from app.models.assessment_session import SessionStatus
from app.models.chat import MessageRole
from app.services.assessment_agent import (
    is_crisis_message,
    recommend_assessment_types,
)
from app.services.assessment_session_service import (
    create_offered_session,
    get_active_session as get_assessment_session,
    get_assessment_context_for_rag,
    get_session_state,
)
from app.services.chroma_service import retrieve_context, retrieve_patient_memory
from app.services.deepgram_service import transcribe_audio
from app.services.escalation_service import handle_critical_escalation
from app.services.openrouter_client import chat_completion
from app.services.risk_service import analyze_message_risk, should_trigger_assessment
from app.services.sentiment_service import analyze_sentiment
from app.services.socket_service import broadcast_patient_update, broadcast_risk_alert
from app.utils.helpers import first_name
from app.utils.i18n import (
    assessment_offer_message,
    crisis_reply,
    normalize_language,
    tech_difficulty_reply,
)
from app.utils.keywords import keyword_score
from app.utils.prompts import build_rag_prompt, greeting_message
from app.utils.session_helpers import get_active_session as get_chat_session

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _patient():
    user = User.query.get(int(get_jwt_identity()))
    return user.patient if user else None


def _process_message(patient, content: str, is_voice: bool = False, language: str = "en"):
    language = normalize_language(language)
    if not patient.consent_given:
        return None, {"error": "Consent required", "code": "CONSENT_REQUIRED"}, 403

    chat_session = get_chat_session(patient)
    user_msg = ChatMessage(
        session_id=chat_session.id,
        patient_id=patient.id,
        role=MessageRole.PATIENT,
        content=content,
        is_voice=is_voice,
    )
    db.session.add(user_msg)
    db.session.flush()

    sentiment_data = analyze_sentiment(content)
    db.session.add(
        SentimentAnalysis(
            patient_id=patient.id,
            message_id=user_msg.id,
            sentiment_score=sentiment_data["score"],
            sentiment_label=sentiment_data["sentiment"],
        )
    )

    kw = keyword_score(content)
    risk = analyze_message_risk(patient.id, user_msg.id, content)
    msg_count = ChatMessage.query.filter_by(patient_id=patient.id).count()
    crisis = is_crisis_message(content, kw)
    counselor_mode = patient.ai_active is False

    # Patient asked for human / counselor support
    lower = content.lower()
    if any(k in lower for k in ("counselor", "human", "real person", "talk to someone", "speak to someone")):
        try:
            from app.services.notification_service import notify_counselor_mentioned
            notify_counselor_mentioned(patient, "Patient requested counselor support in chat")
        except Exception:
            pass

    assessment_offer = None
    crisis_mode = False
    counselor_takeover = counselor_mode
    ctx_ids = None
    reply = ""

    if counselor_mode and not crisis and not risk.suicide_flag:
        broadcast_patient_update(patient.id, {
            "event": "patient_message",
            "patient_id": patient.id,
            "patient_name": patient.full_name,
            "risk_score": risk.risk_score,
            "risk_level": risk.risk_level,
        })
        reply = ""
    elif crisis or risk.suicide_flag:
        crisis_mode = True
        if risk.risk_level == "Critical":
            handle_critical_escalation(patient, risk)
            counselor_takeover = True
        broadcast_risk_alert(patient, risk)
        reply = crisis_reply(language)
    else:
        if risk.risk_level in ("High", "Critical"):
            broadcast_risk_alert(patient, risk)
        else:
            broadcast_patient_update(patient.id, {
                "event": "patient_update",
                "patient_id": patient.id,
                "patient_name": patient.full_name,
                "risk_score": risk.risk_score,
                "risk_level": risk.risk_level,
                "sentiment": sentiment_data,
            })

        active = get_assessment_session(patient.id)
        in_progress = active and active.status in (
            SessionStatus.IN_PROGRESS,
            SessionStatus.ACCEPTED,
        )
        offer_assessment = should_trigger_assessment(patient.id, risk.risk_score, msg_count) and not in_progress

        if offer_assessment:
            types = recommend_assessment_types(content, risk.risk_score)
            offered = create_offered_session(patient.id, types)
            db.session.flush()
            reply = assessment_offer_message(first_name(patient.full_name), language)
            assessment_offer = {
                "offered": True,
                "session_id": offered.id,
                "types": types,
                "message": reply,
            }
        else:
            history = [
                {"role": m.role.value, "content": m.content}
                for m in ChatMessage.query.filter_by(session_id=chat_session.id)
                .order_by(ChatMessage.created_at.asc())
                .all()
            ]
            chunks, ctx_ids = retrieve_context(content)
            memory = retrieve_patient_memory(patient.patient_id, content)
            assess_ctx = get_assessment_context_for_rag(patient.id)
            messages = build_rag_prompt(
                first_name(patient.full_name),
                memory + chunks,
                history[:-1],
                assess_ctx or None,
                language=language,
            )
            messages.append({"role": "user", "content": content})
            try:
                reply = chat_completion(messages)
            except Exception as e:
                reply = tech_difficulty_reply(language, str(e))

    if reply:
        db.session.add(
            ChatMessage(
                session_id=chat_session.id,
                patient_id=patient.id,
                role=MessageRole.ASSISTANT,
                content=reply,
                rag_context_ids=ctx_ids,
            )
        )
    patient.last_activity_at = datetime.utcnow()
    from app.models.patient import WorkflowStatus

    if patient.workflow_status in (None, WorkflowStatus.RESOLVED.value):
        patient.workflow_status = WorkflowStatus.NEW.value
    db.session.commit()

    active = get_assessment_session(patient.id)
    in_progress = active and active.status == SessionStatus.IN_PROGRESS

    return {
        "user_message_id": user_msg.id,
        "assistant_message": reply if reply else None,
        "sentiment": sentiment_data,
        "risk": {
            "score": risk.risk_score,
            "level": risk.risk_level,
            "breakdown": risk.component_breakdown,
        },
        "assessment_offer": assessment_offer,
        "crisis_mode": crisis_mode,
        "counselor_takeover": counselor_takeover or counselor_mode,
        "ai_active": patient.ai_active is not False,
        "counselor_active": patient.ai_active is False,
        "assessment_session": get_session_state(active) if in_progress and active else None,
        "trigger_assessment": bool(assessment_offer),
    }, None, 200


@chat_bp.get("/greeting")
@jwt_required()
def greeting():
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"greeting": greeting_message(first_name(patient.full_name), request.args.get("language"))})


@chat_bp.post("/message")
@jwt_required()
def message():
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message required"}), 400
    result, err, code = _process_message(patient, content, language=data.get("language", "en"))
    if err:
        return jsonify(err), code
    return jsonify(result)


@chat_bp.post("/voice")
@jwt_required()
def voice():
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    if "audio" not in request.files:
        return jsonify({"error": "Audio file required"}), 400
    f = request.files["audio"]
    try:
        transcript = transcribe_audio(f.read(), f.mimetype or "audio/wav")
    except Exception as e:
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
    if not transcript:
        return jsonify({"error": "No speech detected"}), 400
    lang = request.form.get("language") or request.args.get("language") or "en"
    result, err, code = _process_message(patient, transcript, is_voice=True, language=lang)
    if err:
        return jsonify(err), code
    result["transcript"] = transcript
    return jsonify(result)


@chat_bp.get("/history")
@jwt_required()
def history():
    patient = _patient()
    if not patient:
        return jsonify({"error": "Not found"}), 404
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    q = ChatMessage.query.filter_by(patient_id=patient.id).order_by(ChatMessage.created_at.asc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "messages": [
            {
                "id": m.id,
                "role": m.role.value,
                "content": m.content,
                "is_voice": m.is_voice,
                "created_at": m.created_at.isoformat(),
            }
            for m in pagination.items
        ],
        "total": pagination.total,
        "page": page,
    })
