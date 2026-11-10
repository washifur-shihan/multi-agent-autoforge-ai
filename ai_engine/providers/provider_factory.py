from ai_engine.providers.base_provider import BaseProvider
from ai_engine.providers.openai_client import OpenAIProvider
from ai_engine.providers.claude_client import ClaudeClient
from ai_engine.providers.gemini_client import GeminiClient
from ai_engine.providers.nvidia_client import NvidiaClient
from ai_engine.providers.mistral_client import MistralClient


class ResilientProviderProxy(BaseProvider):
    """
    Wraps a primary AI provider and automatically cascades across all other
    configured providers in Autoforge AI if the primary provider is missing a key,
    times out, hits a rate limit, or returns an error.
    """

    def __init__(self, preferred_name: str, registry: dict, order: list):
        self.preferred_name = preferred_name
        self.registry = registry
        self.order = order

    def _candidate_sequence(self):
        seq = []
        if self.preferred_name in self.registry:
            seq.append(self.preferred_name)
        for name in self.order:
            if name not in seq:
                seq.append(name)
        return seq

    @property
    def is_configured(self) -> bool:
        for name in self._candidate_sequence():
            inst = self.registry[name]()
            if getattr(inst, "is_configured", False):
                return True
        return False

    def generate_response(self, prompt: str, config: dict = None):
        errors = []
        for name in self._candidate_sequence():
            inst = self.registry[name]()
            if not getattr(inst, "is_configured", False):
                continue
            try:
                res = inst.generate_response(prompt, config=config)
                if res.get("status") == "success" and res.get("output"):
                    return res
                errors.append(f"{name}: {res.get('output', 'empty or error response')}")
                print(f"[Autoforge Failover] Provider '{name}' did not succeed, trying next available provider...")
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"[Autoforge Failover] Provider '{name}' raised {e}, trying next available provider...")

        # If no provider succeeded or none were configured
        detail = " | ".join(errors) if errors else "No AI provider API keys are configured in .env."
        return {
            "provider": self.preferred_name,
            "status": "error",
            "output": detail,
            "tokens_used": None,
        }

    def generate_chat_response(self, messages: list, config: dict = None):
        errors = []
        for name in self._candidate_sequence():
            inst = self.registry[name]()
            if not getattr(inst, "is_configured", False):
                continue
            try:
                if hasattr(inst, "generate_chat_response"):
                    res = inst.generate_chat_response(messages, config=config)
                else:
                    transcript = "\n".join(
                        f"{m.get('role', 'user').upper()}: {m.get('content', '')}"
                        for m in messages
                    )
                    res = inst.generate_response(transcript, config=config)

                if res.get("status") == "success" and res.get("output"):
                    return res
                errors.append(f"{name}: {res.get('output', 'empty or error response')}")
                print(f"[Autoforge Chat Failover] Provider '{name}' failed, trying next available provider...")
            except Exception as e:
                errors.append(f"{name}: {e}")
                print(f"[Autoforge Chat Failover] Provider '{name}' raised {e}, trying next available provider...")

        detail = " | ".join(errors) if errors else "No AI provider API keys are configured in .env."
        return {
            "provider": self.preferred_name,
            "status": "error",
            "output": detail,
            "tokens_used": None,
        }

    def generate_image(self, prompt: str, output_dir: str = "generated_projects"):
        gemini = GeminiClient()
        if getattr(gemini, "is_configured", False):
            return gemini.generate_image(prompt, output_dir=output_dir)
        return {
            "provider": "gemini",
            "status": "error",
            "output": "GEMINI_API_KEY is not configured in .env for image generation.",
            "image_path": None,
            "tokens_used": None,
        }


class ProviderFactory:
    """
    Factory class to return resilient AI provider instances for Autoforge AI.
    Every provider is optional: if the requested provider is not configured or fails
    at runtime, ResilientProviderProxy automatically falls back to any other available model.
    """

    PROVIDERS = {
        "openai": OpenAIProvider,
        "mistral": MistralClient,
        "mistral_vibe": MistralClient,
        "gemini": GeminiClient,
        "claude": ClaudeClient,
        "nvidia": NvidiaClient,
    }

    PROVIDER_ORDER = ["mistral", "openai", "gemini", "claude", "nvidia"]

    @staticmethod
    def get_provider(provider_name: str = "openai"):
        provider_name = (provider_name or "openai").lower().strip()
        if provider_name == "mistral_vibe":
            provider_name = "mistral"

        if provider_name not in ProviderFactory.PROVIDERS:
            raise ValueError(f"Unsupported provider: {provider_name}")

        return ResilientProviderProxy(
            preferred_name=provider_name,
            registry=ProviderFactory.PROVIDERS,
            order=ProviderFactory.PROVIDER_ORDER,
        )

    @staticmethod
    def get_provider_status():
        status = {}
        for name, cls in [
            ("openai", OpenAIProvider),
            ("mistral", MistralClient),
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
