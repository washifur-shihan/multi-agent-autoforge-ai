import os
import requests
from dotenv import load_dotenv
from ai_engine.providers.base_provider import BaseProvider

load_dotenv()


class MistralClient(BaseProvider):
    """
    Mistral / Mistral Vibe AI provider implementation for Autoforge AI.
    Supports Mistral API (api.mistral.ai) and Devstral / Mistral Vibe / Codestral models.
    """

    def __init__(self):
        self.api_key = (
            os.getenv("MISTRAL_API_KEY")
            or os.getenv("MISTRAL_VIBE_API_KEY")
        )
        self.model = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def generate_response(self, prompt: str, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "mistral",
                "status": "error",
                "output": "MISTRAL_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            url = "https://api.mistral.ai/v1/chat/completions"
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
                            "You are Autoforge AI (powered by Mistral Vibe AI), "
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
                err_msg = data.get("message") or data.get("detail") or str(data)
                return {
                    "provider": "mistral",
                    "status": "error",
                    "output": f"Mistral API error: {err_msg}",
                    "tokens_used": None,
                }

            usage = data.get("usage", {})
            tokens = usage.get("total_tokens")

            return {
                "provider": "mistral",
                "status": "success",
                "output": data["choices"][0]["message"]["content"],
                "tokens_used": tokens,
            }

        except Exception as e:
            return {
                "provider": "mistral",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }

    def generate_chat_response(self, messages: list, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "mistral",
                "status": "error",
                "output": "MISTRAL_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            url = "https://api.mistral.ai/v1/chat/completions"
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
                err_msg = data.get("message") or data.get("detail") or str(data)
                return {
                    "provider": "mistral",
                    "status": "error",
                    "output": f"Mistral API error: {err_msg}",
                    "tokens_used": None,
                }

            usage = data.get("usage", {})
            tokens = usage.get("total_tokens")

            return {
                "provider": "mistral",
                "status": "success",
                "output": data["choices"][0]["message"]["content"],
                "tokens_used": tokens,
            }

        except Exception as e:
            return {
                "provider": "mistral",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }

