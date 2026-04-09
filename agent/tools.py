"""
tools.py — Four tools available to the MindEase agent.

Tool 1: analyze_emotion      — Classifies emotion & intensity from user text
Tool 2: get_coping_strategy  — Returns structured coping steps from local JSON KB
Tool 3: search_music         — Fetches a real song via iTunes Search API 
Tool 4: log_mood             — Persists the mood entry to a local SQLite journal
"""

import json
import sqlite3
import os
import requests
from datetime import datetime


HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "j-hartmann/emotion-english-distilroberta-base"
)
HF_TOKEN = os.getenv("HF_TOKEN", "")  # Optional — raises rate limit if provided

# Map HF labels → our 5-category schema
HF_TO_INTERNAL = {
    "anger":   "anger",
    "disgust": "anger",
    "fear":    "anxiety",
    "joy":     "neutral",
    "neutral": "neutral",
    "sadness": "sadness",
    "surprise": "neutral",
}

# Chinese / English keyword fallback
KEYWORD_MAP = {
    "anxiety": [
        "anxious", "worried", "nervous", "scared", "fearful", "uneasy", "panic",
    ],
    "sadness": [
        "sad", "cry", "depressed", "hopeless", "heartbroken", "loss", "grief", "lonely",
    ],
    "anger": [
        "angry", "furious", "rage", "annoyed", "frustrated", "hate", "mad",
    ],
    "stress": [
        "stressed", "overwhelmed", "exhausted", "burned out", "pressure", "too much",  "burnout",
    ],
}


def analyze_emotion(text: str) -> dict:
    """
    Classify the dominant emotion and intensity in the user's message.

    Returns:
        {
            "emotion":    str   — one of: anxiety, sadness, anger, stress, neutral
            "intensity":  str   — "low" or "high"
            "confidence": float — 0.0–1.0
            "source":     str   — "hf_api" | "keyword" | "default"
        }
    """
    # --- Attempt HuggingFace API ---
    try:
        headers = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}
        resp = requests.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": text[:512]},
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                top = max(data[0], key=lambda x: x["score"])
                raw   = top["label"].lower()
                score = round(top["score"], 3)
                emotion    = HF_TO_INTERNAL.get(raw, "neutral")
                intensity  = "high" if score > 0.62 else "low"
                return {
                    "emotion":    emotion,
                    "intensity":  intensity,
                    "confidence": score,
                    "source":     "hf_api",
                }
    except Exception as exc:
        print(f"[analyze_emotion] HF API unavailable: {exc}")

    # --- Keyword fallback (handles Chinese + English) ---
    text_lower = text.lower()
    for emotion, keywords in KEYWORD_MAP.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches >= 1:
            intensity = "high" if matches >= 2 else "low"
            return {
                "emotion":    emotion,
                "intensity":  intensity,
                "confidence": 0.65,
                "source":     "keyword",
            }

    return {
        "emotion":    "neutral",
        "intensity":  "low",
        "confidence": 0.50,
        "source":     "default",
    }



_STRATEGIES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "strategies.json"
)


def get_coping_strategy(emotion: str, intensity: str) -> dict:
    """
    Look up a coping strategy from the local knowledge base.

    Args:
        emotion:   one of anxiety | sadness | anger | stress | neutral
        intensity: "low" | "high"

    Returns:
        {"title": str, "steps": list[str], "affirmation": str}
    """
    with open(_STRATEGIES_PATH, "r", encoding="utf-8") as fh:
        kb = json.load(fh)

    emotion   = emotion.lower()
    intensity = intensity.lower()
    category  = kb.get(emotion, kb["neutral"])
    strategy  = category.get(intensity, category.get("low", {}))
    return strategy



# Maps our emotion + intensity → search terms that iTunes handles well
MUSIC_QUERY_MAP = {
    ("anxiety",  "low"):  ("calm piano instrumental", "Music"),
    ("anxiety",  "high"): ("deep breathing meditation music", "Music"),
    ("sadness",  "low"):  ("gentle acoustic healing", "Music"),
    ("sadness",  "high"): ("comforting soft piano", "Music"),
    ("anger",    "low"):  ("chill lo-fi beats relax", "Music"),
    ("anger",    "high"): ("release tension instrumental", "Music"),
    ("stress",   "low"):  ("lo-fi study focus", "Music"),
    ("stress",   "high"): ("nature sounds stress relief", "Music"),
    ("neutral",  "low"):  ("uplifting acoustic morning", "Music"),
    ("neutral",  "high"): ("positive energy instrumental", "Music"),
}


def search_music(emotion: str, intensity: str) -> dict:
    """
    Fetch a real music recommendation from the iTunes Search API
    matched to the user's emotional state.

    This is the 'dynamic' tool — it calls a live external API and parses
    complex JSON to extract the most relevant track.

    Returns:
        {
            "track_name":    str,
            "artist":        str,
            "preview_url":   str | None,   — 30-second audio preview
            "track_url":     str,           — Apple Music / iTunes link
            "artwork_url":   str | None,
            "genre":         str,
            "search_term":   str,
            "source":        "itunes" | "fallback"
        }
    """
    emotion   = emotion.lower()
    intensity = intensity.lower()
    query_term, media_type = MUSIC_QUERY_MAP.get(
        (emotion, intensity), ("relaxing instrumental music", "Music")
    )

    try:
        params = {
            "term":    query_term,
            "media":   "music",
            "entity":  "song",
            "limit":   10,
            "explicit": "No",
        }
        resp = requests.get(
            "https://itunes.apple.com/search",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results", [])
        if not results:
            raise ValueError("No results returned from iTunes API")

        # Pick the best match: prefer tracks that have a preview URL
        candidates = [r for r in results if r.get("previewUrl")]
        track = candidates[0] if candidates else results[0]

        return {
            "track_name":  track.get("trackName", "Unknown"),
            "artist":      track.get("artistName", "Unknown"),
            "preview_url": track.get("previewUrl"),
            "track_url":   track.get("trackViewUrl", ""),
            "artwork_url": track.get(
                "artworkUrl100",
                track.get("artworkUrl60"),
            ),
            "genre":       track.get("primaryGenreName", ""),
            "search_term": query_term,
            "source":      "itunes",
        }

    except Exception as exc:
        print(f"[search_music] iTunes API error: {exc}")

        # Graceful fallback — curated static playlist
        FALLBACK = {
            "anxiety":  {"track_name": "Weightless",       "artist": "Marconi Union"},
            "sadness":  {"track_name": "River Flows in You","artist": "Yiruma"},
            "anger":    {"track_name": "Experience",        "artist": "Ludovico Einaudi"},
            "stress":   {"track_name": "Clair de Lune",     "artist": "Claude Debussy"},
            "neutral":  {"track_name": "Morning Mood",      "artist": "Edvard Grieg"},
        }
        fb = FALLBACK.get(emotion, FALLBACK["neutral"])
        return {
            "track_name":  fb["track_name"],
            "artist":      fb["artist"],
            "preview_url": None,
            "track_url":   "",
            "artwork_url": None,
            "genre":       "Classical / Ambient",
            "search_term": query_term,
            "source":      "fallback",
        }


_DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "journal.db"
)


def _ensure_db() -> None:
    """Create the mood_log table if it doesn't exist yet."""
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mood_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   TEXT    NOT NULL,
            timestamp TEXT    NOT NULL,
            emotion   TEXT,
            intensity TEXT,
            summary   TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_mood(
    user_id:   str,
    emotion:   str,
    intensity: str,
    summary:   str,
) -> dict:
    """
    Persist a mood entry to the local SQLite journal database.

    Returns:
        {"status": "ok", "id": int, "timestamp": str}
    """
    _ensure_db()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(_DB_PATH)
    cur  = conn.execute(
        "INSERT INTO mood_log (user_id, timestamp, emotion, intensity, summary) "
        "VALUES (?, ?, ?, ?, ?)",
        (user_id, timestamp, emotion, intensity, summary[:250]),
    )
    conn.commit()
    entry_id = cur.lastrowid
    conn.close()
    return {"status": "ok", "id": entry_id, "timestamp": timestamp}



TOOLS: dict = {
    "analyze_emotion":    analyze_emotion,
    "get_coping_strategy": get_coping_strategy,
    "search_music":       search_music,
    "log_mood":           log_mood,
}

# Human-readable schema (for reference / eval)
TOOL_SCHEMAS: list[dict] = [
    {
        "name": "analyze_emotion",
        "description": "Classify the dominant emotion and intensity in the user's message.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Raw user message to analyze"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "get_coping_strategy",
        "description": "Return structured coping steps from the local knowledge base.",
        "parameters": {
            "type": "object",
            "properties": {
                "emotion":   {"type": "string", "enum": ["anxiety","sadness","anger","stress","neutral"]},
                "intensity": {"type": "string", "enum": ["low","high"]},
            },
            "required": ["emotion","intensity"],
        },
    },
    {
        "name": "search_music",
        "description": (
            "Fetch a real, mood-matched song from the iTunes Search API. "
            "Returns track name, artist, 30-second preview URL, and artwork."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "emotion":   {"type": "string", "enum": ["anxiety","sadness","anger","stress","neutral"]},
                "intensity": {"type": "string", "enum": ["low","high"]},
            },
            "required": ["emotion","intensity"],
        },
    },
    {
        "name": "log_mood",
        "description": "Save the current mood entry to the local SQLite journal.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id":   {"type": "string"},
                "emotion":   {"type": "string"},
                "intensity": {"type": "string"},
                "summary":   {"type": "string", "description": "1-2 sentence summary of this turn"},
            },
            "required": ["user_id","emotion","intensity","summary"],
        },
    },
]
