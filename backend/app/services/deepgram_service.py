import os

from flask import current_app


def transcribe_audio(audio_bytes: bytes, mimetype: str = "audio/wav") -> str:
    api_key = current_app.config.get("DEEPGRAM_API_KEY") or os.getenv("DEEPGRAM_API_KEY", "")
    if not api_key:
        raise ValueError("Deepgram API key not configured")
    from deepgram import DeepgramClient, PrerecordedOptions

    client = DeepgramClient(api_key)
    options = PrerecordedOptions(model="nova-2", smart_format=True, language="en")
    payload = {"buffer": audio_bytes, "mimetype": mimetype}
    response = client.listen.rest.v("1").transcribe_file(payload, options)
    transcript = response.results.channels[0].alternatives[0].transcript
    return transcript.strip()
