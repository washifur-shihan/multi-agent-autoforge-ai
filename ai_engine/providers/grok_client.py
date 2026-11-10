import os
import requests
from dotenv import load_dotenv
from ai_engine.providers.base_provider import BaseProvider

load_dotenv(override=True)


class GrokClient(BaseProvider):
    """
    Grok (xAI) & Groq Cloud provider implementation for Autoforge AI.
    Automatically discovers and falls back across available models on your account
    if a default model is deprecated or restricted.
    """

    GROQ_CANDIDATE_MODELS = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]

    XAI_CANDIDATE_MODELS = [
        "grok-3-latest",
        "grok-2-latest",
        "grok-beta",
    ]

    def __init__(self):
        load_dotenv(override=True)
        self.api_key = (
            os.getenv("GROK_API_KEY")
            or os.getenv("XAI_API_KEY")
            or os.getenv("GROQ_API_KEY")
        )
        self._is_groq_cloud = bool(
            (self.api_key and self.api_key.strip().startswith("gsk_"))
            or (not os.getenv("GROK_API_KEY") and not os.getenv("XAI_API_KEY") and os.getenv("GROQ_API_KEY"))
        )
        env_model = (os.getenv("GROK_MODEL") or "").strip()

        if self._is_groq_cloud:
            if not env_model or env_model.startswith("grok"):
                self.model = "openai/gpt-oss-120b"
            else:
                self.model = env_model
        else:
            self.model = env_model or "grok-3-latest"

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def _endpoint_url(self) -> str:
        if self._is_groq_cloud:
            return "https://api.groq.com/openai/v1/chat/completions"
        return "https://api.x.ai/v1/chat/completions"

    def _models_to_try(self, config: dict = None) -> list:
        primary = config.get("model") if config and config.get("model") else self.model
        candidates = self.GROQ_CANDIDATE_MODELS if self._is_groq_cloud else self.XAI_CANDIDATE_MODELS
        seq = [primary]
        for m in candidates:
            if m not in seq:
                seq.append(m)
        return seq

    def generate_response(self, prompt: str, config: dict = None):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Autoforge AI, "
                    "an autonomous software engineering, coding, and research assistant."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        return self.generate_chat_response(messages, config=config)

    def generate_chat_response(self, messages: list, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "grok",
                "status": "error",
                "output": "GROK_API_KEY (or GROQ_API_KEY) is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        url = self._endpoint_url()
        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }

        last_err = None
        for model in self._models_to_try(config):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                data = response.json()

                if response.status_code == 200 and "choices" in data and data["choices"]:
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens")
                    return {
                        "provider": "grok",
                        "model": model,
                        "status": "success",
                        "output": data["choices"][0]["message"]["content"],
                        "tokens_used": tokens,
                    }

                err_obj = data.get("error") or data.get("message") or data
                last_err = f"Grok API error ({model}): {err_obj}"
                # If model_not_found or decommissioned, try the next candidate model on this account
                if "model_not_found" in str(err_obj) or "decommissioned" in str(err_obj) or "does not exist" in str(err_obj):
                    continue
                break

            except Exception as e:
                last_err = str(e)
                break

        return {
            "provider": "grok",
            "status": "error",
            "output": last_err or "Unknown Grok API error",
            "tokens_used": None,
        }
