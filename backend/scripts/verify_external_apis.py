"""Verify OpenRouter and Deepgram API connectivity (keys from .env)."""
from __future__ import annotations

import os
import sys
import wave
import struct
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _make_test_wav() -> bytes:
    """Generate a short sine-tone WAV for Deepgram smoke test."""
    import io

    sample_rate = 16000
    duration = 0.5
    freq = 440.0
    n = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        for i in range(n):
            val = int(32767 * 0.3 * math.sin(2 * math.pi * freq * i / sample_rate))
            w.writeframes(struct.pack("<h", val))
    return buf.getvalue()


def test_openrouter() -> tuple[bool, str]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        return False, "OPENROUTER_API_KEY not set in .env"

    try:
        from app.services.openrouter_client import chat_completion

        reply = chat_completion(
            [
                {"role": "system", "content": "Reply with exactly: OK"},
                {"role": "user", "content": "ping"},
            ]
        )
        if reply and len(reply.strip()) > 0:
            return True, f"OK — model replied ({len(reply)} chars)"
        return False, "Empty response from OpenRouter"
    except Exception as e:
        return False, str(e)[:300]


def test_deepgram() -> tuple[bool, str]:
    key = os.getenv("DEEPGRAM_API_KEY", "").strip()
    if not key:
        return False, "DEEPGRAM_API_KEY not set in .env"

    try:
        from app import create_app
        from app.services.deepgram_service import transcribe_audio

        app = create_app()
        with app.app_context():
            audio = _make_test_wav()
            try:
                transcript = transcribe_audio(audio, "audio/wav")
                return True, f"API reachable — transcript: {transcript[:80] or '(empty, tone only)'}"
            except ValueError as e:
                msg = str(e)
                if "No speech detected" in msg:
                    return True, "API reachable (no speech in test tone — expected)"
                if "Invalid Deepgram API key" in msg or "401" in msg:
                    return False, "Invalid Deepgram API key"
                if "quota" in msg.lower():
                    return False, msg
                return False, msg[:300]
    except Exception as e:
        return False, str(e)[:300]


def main():
    print("EchoSense external API verification\n" + "=" * 40)
    ok_or, msg_or = test_openrouter()
    print(f"OpenRouter: {'PASS' if ok_or else 'FAIL'}")
    print(f"  {msg_or}\n")

    ok_dg, msg_dg = test_deepgram()
    print(f"Deepgram:   {'PASS' if ok_dg else 'FAIL'}")
    print(f"  {msg_dg}\n")

    if ok_or and ok_dg:
        print("All configured APIs are working.")
        return 0
    print("One or more APIs failed — check .env keys and quotas.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
