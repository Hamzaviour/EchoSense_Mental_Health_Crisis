"""English + Roman Urdu strings for patient-facing responses."""

SUPPORTED = frozenset({"en", "ur"})


def normalize_language(lang: str | None) -> str:
    if not lang:
        return "en"
    lower = lang.lower().strip()
    if lower in ("ur", "ur-roman", "roman-urdu", "roman_urdu", "urdu"):
        return "ur"
    return "en"


def language_instruction(lang: str) -> str:
    lang = normalize_language(lang)
    if lang == "ur":
        return (
            "IMPORTANT: Respond in Roman Urdu (Urdu written in English/Latin letters, "
            "e.g. 'Aap kaise mehsoos kar rahe hain?'). Do NOT use Arabic/Urdu script. "
            "Match the language of the patient's latest message — if they write in English, "
            "reply in English; if they write in Roman Urdu, reply in Roman Urdu."
        )
    return (
        "IMPORTANT: Respond in English. Match the language of the patient's latest message — "
        "if they write in Roman Urdu, reply in Roman Urdu; if they write in English, reply in English."
    )


def greeting_message(first_name: str, lang: str = "en") -> str:
    lang = normalize_language(lang)
    if lang == "ur":
        return (
            f"Assalam o Alaikum {first_name}. Main Echo Sense Assistant hoon. "
            "Main yahan hoon aap ki sunne aur support karne ke liye. Aaj aap kaise mehsoos kar rahe hain?"
        )
    return (
        f"Hello {first_name}. I am Echo Sense Assistant. "
        "I am here to listen and support you. How are you feeling today?"
    )


def crisis_reply(lang: str = "en") -> str:
    lang = normalize_language(lang)
    if lang == "ur":
        return (
            "Mujhe khushi hai ke aap ne yeh share kiya. Aap akelay nahi hain, aur jo mehsoos kar rahe hain "
            "woh important hai. Aap ki baat ki wajah se ek counselor ko inform kar diya gaya hai aur "
            "woh jald rabta kar sakte hain. Agar fori khatra ho to Umang par call karein: 0311-7786264 (24/7). "
            "Kya aap thori der mere saath reh sakte hain?"
        )
    return (
        "I'm really glad you told me this. You're not alone, and what you're feeling matters. "
        "Because of what you've shared, a counselor has been notified and may reach out very soon. "
        "If you're in immediate danger, please call Umang at 0311-7786264 (24/7). "
        "Would you stay with me for a moment?"
    )


def assessment_offer_message(first_name: str, lang: str = "en") -> str:
    lang = normalize_language(lang)
    if lang == "ur":
        return (
            f"Share karne ka shukriya, {first_name}. Aap ke feelings ko behtar samajhne ke liye, "
            "main kuch chhote sawaal poochna chahta/chahti hoon jo mental health professionals aksar use karte hain. "
            "Is mein do minute se kam lagte hain. Kya yeh theek hai?"
        )
    return (
        f"Thank you for sharing that, {first_name}. To better understand how these feelings "
        "have been affecting you, I'd like to ask a few brief questions that are commonly used "
        "by mental health professionals. It usually takes less than two minutes. Would that be okay?"
    )


def tech_difficulty_reply(lang: str = "en", detail: str = "") -> str:
    lang = normalize_language(lang)
    suffix = f" ({detail[:80]})" if detail else ""
    if lang == "ur":
        return (
            "Main yahan hoon aap ke saath. Thori technical problem hai, "
            f"lekin aap ka message receive ho gaya hai.{suffix}"
        )
    return (
        "I'm here with you. I'm having a brief technical difficulty, "
        f"but your message has been received.{suffix}"
    )
