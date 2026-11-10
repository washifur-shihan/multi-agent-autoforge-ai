import os
from dotenv import load_dotenv
from openai import OpenAI

from ai_engine.providers.base_provider import BaseProvider

load_dotenv()


class OpenAIProvider(BaseProvider):
    """
    OpenAI provider implementation for Autoforge AI.
    Handles communication with OpenAI models with graceful fallback when unconfigured.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def generate_response(self, prompt: str, config: dict = None):
        """
        Generate response from OpenAI.

        Args:
            prompt (str): Input prompt
            config (dict): Optional model configuration

        Returns:
            dict: Standardized response
        """
        if not self.is_configured:
            return {
                "provider": "openai",
                "status": "error",
                "output": "OPENAI_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

            if config and "model" in config:
                model = config["model"]

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are Autoforge AI, a helpful and precise autonomous software engineering and research assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            output_text = response.choices[0].message.content

            return {
                "provider": "openai",
                "status": "success",
                "output": output_text,
                "tokens_used": response.usage.total_tokens if response.usage else None,
            }

        except Exception as e:
            return {
                "provider": "openai",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }

    def generate_chat_response(self, messages: list, config: dict = None):
        """
        Generate response from OpenAI using a conversation history.

        Args:
            messages (list): List of message dictionaries containing "role" and "content"
            config (dict): Optional model configuration

        Returns:
            dict: Standardized response
        """
        if not self.is_configured:
            return {
                "provider": "openai",
                "status": "error",
                "output": "OPENAI_API_KEY is not configured in environment variables (.env).",
                "tokens_used": None,
            }

        try:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

            if config and "model" in config:
                model = config["model"]

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )

            output_text = response.choices[0].message.content

            return {
                "provider": "openai",
                "status": "success",
                "output": output_text,
                "tokens_used": response.usage.total_tokens if response.usage else None,
            }

        except Exception as e:
            return {
                "provider": "openai",
                "status": "error",
                "output": str(e),
                "tokens_used": None,
            }
