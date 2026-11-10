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

            # ProviderFactory.get_provider() returns a ResilientProviderProxy that
            # already cascades across all configured providers (mistral, grok, openai, gemini, claude, nvidia).
            provider = ProviderFactory.get_provider(provider_name)

            if task_type == "image_generation":
                response = provider.generate_image(intent)
            else:
                response = provider.generate_response(final_prompt)

            results.append({
                "task_type": task_type,
                "provider": response.get("provider", provider_name),
                "result": response
            })

        return {
            "results": results
        }
