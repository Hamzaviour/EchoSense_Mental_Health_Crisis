import logging
import os

from flask import current_app

logger = logging.getLogger(__name__)

# Map browser MediaRecorder types to Deepgram-friendly MIME hints (SDK sends octet-stream body).
MIME_NORMALIZE = {
    "audio/webm": "audio/webm",
    "audio/webm;codecs=opus": "audio/webm",
    "audio/ogg": "audio/ogg",
    "audio/ogg;codecs=opus": "audio/ogg",
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
    "audio/mpeg": "audio/mpeg",
    "audio/mp4": "audio/mp4",
}


def _extract_transcript(response) -> str:
    """Parse transcript from Deepgram SDK v3 or v7 response objects."""
    try:
        channels = response.results.channels
        if channels:
            alts = channels[0].alternatives
            if alts and alts[0].transcript:
                return (alts[0].transcript or "").strip()
    except AttributeError:
        pass

    if hasattr(response, "model_dump"):
        data = response.model_dump()
    elif hasattr(response, "dict"):
        data = response.dict()
    else:
        return ""

    try:
        return (
            data.get("results", {})
            .get("channels", [{}])[0]
            .get("alternatives", [{}])[0]
            .get("transcript", "")
            or ""
        ).strip()
    except (IndexError, TypeError, AttributeError):
        return ""


def _transcribe_v7(audio_bytes: bytes, api_key: str, mimetype: str) -> str:
    from deepgram import DeepgramClient

    client = DeepgramClient(api_key=api_key)
    response = client.listen.v1.media.transcribe_file(
        request=audio_bytes,
        model="nova-2",
        smart_format=True,
        language="en",
        punctuate=True,
    )
    transcript = _extract_transcript(response)
    if not transcript:
        raise ValueError("No speech detected in recording")
    return transcript


def _transcribe_v3(audio_bytes: bytes, api_key: str, mimetype: str) -> str:
    from deepgram import DeepgramClient, PrerecordedOptions

    client = DeepgramClient(api_key)
    options = PrerecordedOptions(model="nova-2", smart_format=True, language="en")
    payload = {"buffer": audio_bytes, "mimetype": mimetype}
    response = client.listen.rest.v("1").transcribe_file(payload, options)
    transcript = _extract_transcript(response)
    if not transcript:
        raise ValueError("No speech detected in recording")
    return transcript


def transcribe_audio(audio_bytes: bytes, mimetype: str = "audio/wav") -> str:
    api_key = current_app.config.get("DEEPGRAM_API_KEY") or os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError(
            "Deepgram API key not configured. Add DEEPGRAM_API_KEY to your .env file."
        )
    if not audio_bytes or len(audio_bytes) < 100:
        raise ValueError("Audio recording is empty or too short")

    mimetype = MIME_NORMALIZE.get((mimetype or "").split(";")[0].strip().lower(), mimetype or "audio/webm")

    try:
        from deepgram import DeepgramClient  # noqa: F401

        return _transcribe_v7(audio_bytes, api_key, mimetype)
    except ImportError as exc:
        if "PrerecordedOptions" in str(exc):
            raise ValueError(
                "Incompatible deepgram-sdk version. Run: pip install 'deepgram-sdk>=7.0,<8'"
            ) from exc
        raise
    except Exception as exc:
        err = str(exc)
        logger.exception("Deepgram transcription failed: %s", err)
        if "PrerecordedOptions" in err:
            try:
                return _transcribe_v3(audio_bytes, api_key, mimetype)
            except ImportError:
                pass
        if "401" in err or "Unauthorized" in err:
            raise ValueError("Invalid Deepgram API key") from exc
        if "402" in err or "payment" in err.lower():
            raise ValueError("Deepgram account quota exceeded") from exc
        raise ValueError(f"Transcription failed: {err[:200]}") from exc
