from ai_engine.providers.openai_client import OpenAIProvider
from ai_engine.providers.claude_client import ClaudeClient
from ai_engine.providers.gemini_client import GeminiClient
from ai_engine.providers.nvidia_client import NvidiaClient


class ProviderFactory:
    """
    Factory class to return the correct AI provider instance for Aurora Agent AI.
    Supports automatic fallback to any configured provider.
    """

    PROVIDER_ORDER = ["openai", "gemini", "claude", "nvidia"]

    @staticmethod
    def get_provider(provider_name: str):
        provider_name = (provider_name or "openai").lower().strip()

        providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeClient,
            "gemini": GeminiClient,
            "nvidia": NvidiaClient,
        }

        if provider_name not in providers:
            raise ValueError(f"Unsupported provider: {provider_name}")

        instance = providers[provider_name]()
        if getattr(instance, "is_configured", False):
            return instance

        # If requested provider is not configured, try other configured providers
        for alt_name in ProviderFactory.PROVIDER_ORDER:
            if alt_name == provider_name:
                continue
            alt_instance = providers[alt_name]()
            if getattr(alt_instance, "is_configured", False):
                return alt_instance

        # Return requested instance (which will return a clean unconfigured status dict)
        return instance

    @staticmethod
    def get_provider_status():
        status = {}
        for name, cls in [
            ("openai", OpenAIProvider),
            ("gemini", GeminiClient),
            ("claude", ClaudeClient),
            ("nvidia", NvidiaClient),
        ]:
            try:
                inst = cls()
                status[name] = bool(getattr(inst, "is_configured", False))
            except Exception:
                status[name] = False
        return status
