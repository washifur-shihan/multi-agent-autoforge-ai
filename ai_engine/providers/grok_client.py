import os
import requests
from dotenv import load_dotenv
from ai_engine.providers.base_provider import BaseProvider

load_dotenv()


class GrokClient(BaseProvider):
    """
    Grok (xAI) & Groq Cloud provider implementation for Autoforge AI.
    Supports both:
      - Groq Cloud (https://api.groq.com/openai/v1/chat/completions) for keys starting with 'gsk_'
      - xAI Grok (https://api.x.ai/v1/chat/completions) for xAI keys
    """

    def __init__(self):
        self.api_key = (
            os.getenv("GROK_API_KEY")
            or os.getenv("XAI_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )
        # Detect if user supplied a Groq (gsk_...) key vs xAI Grok (xai-...) key
        self._is_groq_cloud = bool(
            (self.api_key and self.api_key.strip().startswith("gsk_"))
            or (not os.getenv("GROK_API_KEY") and not os.getenv("XAI_API_KEY") and os.getenv("GROQ_API_KEY"))
        )
        env_model = (os.getenv("GROK_MODEL") or "").strip()

        # If a Groq Cloud key (gsk_) is used, ensure we don't send an xAI-only model name like grok-2-latest
        if self._is_groq_cloud:
            if not env_model or env_model.startswith("grok"):
                self.model = "llama-3.3-70b-versatile"
            else:
                self.model = env_model
        else:
            self.model = env_model or "grok-2-latest"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _endpoint_url(self) -> str:
        if self._is_groq_cloud:
            return "https://api.groq.com/openai/v1/chat/completions"
        return "https://api.x.ai/v1/chat/completions"

    def generate_response(self, prompt: str, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "grok",
                "status": "error",
                "output": "GROK_API_KEY (or GROQ_API_KEY) is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            url = self._endpoint_url()
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json",
            }

            model = config.get("model") if config and config.get("model") else self.model

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are Autoforge AI, "
                            "an autonomous software engineering, coding, and research assistant."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=90)
            data = response.json()

            if response.status_code != 200 or "choices" not in data or not data["choices"]:
                err_msg = data.get("error") or data.get("message") or str(data)
                return {
                    "provider": "grok",
                    "status": "error",
                    "output": f"Grok API error: {err_msg}",
                    "tokens_used": None,
                }

            usage = data.get("usage", {})
            tokens = usage.get("total_tokens")

            return {
                "provider": "grok",
                "status": "success",
                "output": data["choices"][0]["message"]["content"],
                "tokens_used": tokens,
            }

        except Exception as e:
            return {
                "provider": "grok",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }

    def generate_chat_response(self, messages: list, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "grok",
                "status": "error",
                "output": "GROK_API_KEY (or GROQ_API_KEY) is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            url = self._endpoint_url()
            headers = {
                "Authorization": f"Bearer {self.api_key.strip()}",
                "Content-Type": "application/json",
            }

            model = config.get("model") if config and config.get("model") else self.model

            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.7,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=90)
            data = response.json()

            if response.status_code != 200 or "choices" not in data or not data["choices"]:
                err_msg = data.get("error") or data.get("message") or str(data)
                return {
                    "provider": "grok",
                    "status": "error",
                    "output": f"Grok API error: {err_msg}",
                    "tokens_used": None,
                }

            usage = data.get("usage", {})
            tokens = usage.get("total_tokens")

            return {
                "provider": "grok",
                "status": "success",
                "output": data["choices"][0]["message"]["content"],
                "tokens_used": tokens,
            }

        except Exception as e:
            return {
                "provider": "grok",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }
