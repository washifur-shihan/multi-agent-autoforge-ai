"""
Aurora Agent AI — Provider Configuration & Default Model Registry
"""

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "gemini_text": "gemini-2.5-flash",
    "gemini_image": "gemini-3.1-flash-image-preview",
    "claude": "claude-sonnet-4-5",
    "nvidia": "meta/llama3-70b-instruct",
}

FALLBACK_PROVIDER_ORDER = ["openai", "gemini", "claude", "nvidia"]
