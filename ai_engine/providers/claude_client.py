from ai_engine.providers.base_provider import BaseProvider
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class ClaudeClient(BaseProvider):

    def __init__(self):
        self.api_key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_response(self, prompt, config=None):
        if not self.is_configured:
            return {
                "provider": "claude",
                "status": "error",
                "output": "CLAUDE_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None
            }

        try:
            url = "https://api.anthropic.com/v1/messages"

            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }

            model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
            if config and "model" in config:
                model = config["model"]

            payload = {
                "model": model,
                "max_tokens": 16000,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(url, json=payload, headers=headers, timeout=90)
            data = response.json()

            if "content" not in data:
                return {
                    "provider": "claude",
                    "status": "error",
                    "output": str(data),
                    "tokens_used": None
                }

            usage = data.get("usage", {})
            tokens = (usage.get("input_tokens", 0) + usage.get("output_tokens", 0)) or None

            return {
                "provider": "claude",
                "status": "success",
                "output": data["content"][0]["text"],
                "tokens_used": tokens
            }
        except Exception as e:
            return {
                "provider": "claude",
                "status": "error",
                "output": str(e),
                "tokens_used": None
            }

    def generate_chat_response(self, messages: list, config: dict = None):
        if not self.is_configured:
            return {
                "provider": "claude",
                "status": "error",
                "output": "CLAUDE_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None
            }
        transcript = "\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
            for m in messages
        )
        return self.generate_response(transcript, config=config)
