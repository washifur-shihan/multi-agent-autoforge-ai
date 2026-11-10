from ai_engine.providers.base_provider import BaseProvider
import requests
import os
from dotenv import load_dotenv

load_dotenv()


class NvidiaClient(BaseProvider):

    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_response(self, prompt, config=None):
        if not self.is_configured:
            return {
                "provider": "nvidia",
                "status": "error",
                "output": "NVIDIA_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None
            }

        try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "meta/llama3-70b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)
            data = response.json()

            if "choices" not in data or not data["choices"]:
                return {
                    "provider": "nvidia",
                    "status": "error",
                    "output": str(data),
                    "tokens_used": None
                }

            return {
                "provider": "nvidia",
                "status": "success",
                "output": data["choices"][0]["message"]["content"],
                "tokens_used": None
            }
        except Exception as e:
            return {
                "provider": "nvidia",
                "status": "error",
                "output": str(e),
                "tokens_used": None
            }
