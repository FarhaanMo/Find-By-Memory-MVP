"""Optional Groq key. Never hardcoded and never logged."""

import os
from pathlib import Path

from dotenv import load_dotenv

MVP_ROOT = Path(__file__).resolve().parents[1]


def get_groq_api_key():
    load_dotenv(MVP_ROOT / ".env")
    load_dotenv()
    env_key = os.environ.get("GROQ_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    try:
        import streamlit as st

        secret = st.secrets.get("GROQ_API_KEY")
    except Exception:
        return None
    if secret and str(secret).strip():
        return str(secret).strip()
    return None
