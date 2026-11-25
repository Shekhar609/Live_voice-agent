import re
from typing import Dict, Tuple

# Common Hindi romanized words (Hinglish dictionary for code-switching detection)
COMMON_HINGLISH_WORDS = {
    "aap", "hum", "tum", "kya", "kaise", "kaisa", "kaisi", "hai", "hain", "ho", "tha", "thi", "the",
    "kar", "karo", "karenge", "karna", "raha", "rahe", "rahi", "hoga", "hogi", "bhi", "aur", "ya",
    "lekin", "magar", "kyunki", "isliye", "jab", "tab", "ab", "kab", "kaha", "idhar", "udhar",
    "mujhe", "tumhe", "unhe", "usse", "isse", "mera", "meri", "mere", "tera", "teri", "tere",
    "apna", "apni", "apne", "bahut", "bohot", "accha", "achha", "theek", "shukriya", "dhanyawad",
    "namaste", "namaskar", "alvida", "dost", "yaar", "bhai", "log", "kam", "kaam", "ghar", "samay",
    "waqt", "aaj", "kal", "parso", "subah", "shaam", "raat", "suno", "bolo", "dekho", "samjhe",
    "chal", "chalo", "ruko", "baat", "cheez", "pata", "nhi", "nahi", "matlab", "shuru"
}

def is_devanagari_char(char: str) -> bool:
    """Check if a unicode character belongs to the Devanagari script (Unicode range 0x0900 - 0x097F)."""
    return '\u0900' <= char <= '\u097F'

def analyze_multilingual_text(text: str) -> Tuple[str, str, Dict[str, float]]:
    """
    Analyzes input transcribed text to determine if it is:
    - Hindi (Devanagari script)
    - English (Pure English)
    - Hinglish / Multilingual (Mixed Hindi and English words)
    
    Returns:
    - detected_language label (e.g. "Hinglish (Hindi + English)", "Hindi", "English")
    - breakdown string (e.g. "Hindi: 60%, English: 40%")
    - percentage breakdown dictionary
    """
    if not text or not text.strip():
        return "Unknown", "N/A", {"hindi": 0.0, "english": 0.0}

    # Count devanagari characters
    devanagari_chars = sum(1 for c in text if is_devanagari_char(c))
    total_letters = sum(1 for c in text if c.isalpha())

    words = re.findall(r'\b[a-zA-Z\u0900-\u097F]+\b', text.lower())
    if not words:
        return "English", "English: 100%", {"hindi": 0.0, "english": 100.0}

    hindi_word_count = 0
    english_word_count = 0

    for word in words:
        # Check if word contains devanagari
        if any(is_devanagari_char(c) for c in word):
            hindi_word_count += 1
        elif word in COMMON_HINGLISH_WORDS:
            hindi_word_count += 1
        else:
            english_word_count += 1

    total_words = len(words)
    hindi_pct = round((hindi_word_count / total_words) * 100, 1)
    english_pct = round((english_word_count / total_words) * 100, 1)

    # Determine classification
    if devanagari_chars > (total_letters * 0.7) if total_letters > 0 else False:
        detected_language = "Hindi (Devanagari)"
    elif hindi_pct >= 20.0 and english_pct >= 20.0:
        detected_language = "Hinglish (Hindi + English)"
    elif hindi_pct > 60.0:
        detected_language = "Hindi"
    elif english_pct > 80.0:
        detected_language = "English"
    else:
        detected_language = "Multilingual (Hindi/English)"

    breakdown_str = f"Hindi: {hindi_pct}%, English: {english_pct}%"
    breakdown_dict = {"hindi": hindi_pct, "english": english_pct}

    return detected_language, breakdown_str, breakdown_dict
