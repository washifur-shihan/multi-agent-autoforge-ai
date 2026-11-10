from ai_engine.providers.provider_factory import ProviderFactory
from ai_engine.prompts.prompt_manager import PromptManager
from ai_engine.prompts.prompt_builder import PromptBuilder


class ExecutionManager:
    """
    Executes tasks in the execution plan with multi-provider fallback.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def execute(self, execution_plan, architecture=None):
        if architecture is None:
            architecture = {}

        results = []

        for task in execution_plan.get("execution_plan", []):
            provider_name = task.get("provider", "openai")
            task_type = task.get("task_type", "chat")
            if task_type == "image_generation":
                provider_name = "gemini"
            intent = task.get("intent", "")

            # Build prompts
            base_prompt = PromptManager.get_prompt(task_type, intent)
            structured_prompt = self.prompt_builder.build_prompt(task, architecture)
            final_prompt = base_prompt + "\n" + structured_prompt

            try:
                provider = ProviderFactory.get_provider(provider_name)
                response = provider.generate_response(final_prompt)

                if response.get("status") == "error":
                    print(f"[{provider_name.upper()} ERROR] {response.get('output')} - Attempting Fallback...")
                    raise Exception(response.get("output") or "Provider returned error status.")

            except Exception as e:
                if task_type == "image_generation":
                    response = {
                        "provider": "gemini",
                        "status": "error",
                        "output": f"Gemini image generation failed: {e}",
                        "tokens_used": None
                    }
                else:
                    response = self._attempt_fallbacks(provider_name, final_prompt, e)

            results.append({
                "task_type": task_type,
                "provider": response.get("provider", provider_name),
                "result": response
            })

        return {
            "results": results
        }

    def _attempt_fallbacks(self, failed_provider: str, final_prompt: str, primary_error: Exception):
        fallback_order = ["mistral", "openai", "gemini", "claude", "nvidia"]
        last_error = str(primary_error)

        for alt_name in fallback_order:
            if alt_name == failed_provider:
                continue
            try:
                alt_provider = ProviderFactory.get_provider(alt_name)
                if not getattr(alt_provider, "is_configured", False):
                    continue
                print(f"[EXECUTION FALLBACK] Trying configured provider: {alt_name}")
                resp = alt_provider.generate_response(final_prompt)
                if resp.get("status") == "success":
                    return resp
                last_error = resp.get("output", last_error)
            except Exception as fallback_e:
                last_error = str(fallback_e)

        return {
            "provider": failed_provider,
            "status": "error",
            "output": f"No configured AI provider succeeded. Details: {last_error}",
            "tokens_used": None
        }
