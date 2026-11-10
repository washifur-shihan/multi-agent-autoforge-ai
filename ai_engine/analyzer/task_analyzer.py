from ai_engine.providers.provider_factory import ProviderFactory
import json


class TaskAnalyzer:
    """
    Task Analyzer for Autoforge AI.
    Uses configured LLM provider to analyze user prompts and detect one or multiple tasks,
    with deterministic keyword-based heuristic fallback when no LLM provider is configured.
    """

    def __init__(self):
        self.provider = ProviderFactory.get_provider("gemini")

    def analyze(self, user_prompt: str):
        """
        Analyze the user prompt and return detected tasks.
        """
        analyzer_prompt = f"""
You are an AI task analyzer for Autoforge AI.

Your job is to analyze user prompts and identify tasks.

Supported task types:
- conversation
- website
- web_app
- slides
- research
- design
- automation
- image_generation

Rules:
1. Detect if the prompt contains multiple tasks.
2. Assign a task_type to each task.
3. Assign execution priority (1 = first).
4. Return ONLY valid JSON.
5. Do NOT include 'slides' unless the user explicitly asks for a presentation or slides.
6. If the user asks to generate, create, draw, or make an image, picture, photo, cartoon, logo, poster, avatar, or illustration, use task_type "image_generation".

User prompt:
{user_prompt}

Example output:

{{
 "tasks":[
   {{
     "task_type":"website",
     "intent":"build landing page",
     "priority":1
   }}
 ]
}}
"""

        # Refresh provider via factory with Gemini as first priority
        self.provider = ProviderFactory.get_provider("gemini")
        response = self.provider.generate_response(analyzer_prompt)

        if response.get("status") != "success":
            fallback_tasks = self._heuristic_analyze(user_prompt)
            return {
                "provider": "heuristic",
                "status": "success",
                "output": json.dumps({"tasks": fallback_tasks}),
                "tokens_used": 0,
            }

        return response

    def _heuristic_analyze(self, prompt: str):
        # Extract only the user request portion if system instructions were prepended
        raw_user_text = prompt
        if "USER REQUEST:" in prompt:
            raw_user_text = prompt.split("USER REQUEST:")[-1].strip()

        text = raw_user_text.lower()
        tasks = []
        priority = 1

        if any(w in text for w in ["website", "portfolio", "landing page", "frontend", "html", "react", "web app", "flask", "fastapi"]):
            tasks.append({"task_type": "website", "intent": raw_user_text, "priority": priority})
            priority += 1
        elif any(w in text for w in ["python script", "automation", "scrape", "monitor", "convert csv", "script"]):
            tasks.append({"task_type": "automation", "intent": raw_user_text, "priority": priority})
            priority += 1

        if any(w in text for w in ["slides", "presentation", "pitch deck"]):
            tasks.append({"task_type": "slides", "intent": raw_user_text, "priority": priority})
            priority += 1

        if any(w in text for w in ["research", "report", "impact of", "pdf", "analyze"]):
            tasks.append({"task_type": "research", "intent": raw_user_text, "priority": priority})
            priority += 1

        if not tasks:
            tasks.append({"task_type": "conversation", "intent": raw_user_text, "priority": 1})

        return tasks
