import json
import re


class ArchitecturePlanner:
    """
    Plans software architecture based on detected tasks in Aurora Agent AI.
    Safely handles malformed or empty analyzer outputs.
    """

    def plan(self, analyzer_result):
        architecture = {
            "project_type": None,
            "frontend": {},
            "backend": {},
            "database": None,
            "features": []
        }

        tasks = self._extract_tasks(analyzer_result)

        for task in tasks:
            task_type = str(task.get("task_type", "")).lower().strip()
            intent = str(task.get("intent", "")).lower().strip()

            # ---- AUTOMATION / PYTHON PROJECT ----
            if task_type in ["automation", "python", "script"]:
                architecture["project_type"] = "python_automation"
                architecture["backend"] = {
                    "language": "python",
                    "entry_point": "script.py"
                }
                if "automation_script" not in architecture["features"]:
                    architecture["features"].append("automation_script")

            # ---- WEBSITE / WEB APP PROJECT ----
            elif task_type in ["website", "web_app", "app"]:
                architecture["project_type"] = "fullstack_web_app"

                if "react" in intent:
                    architecture["frontend"] = {
                        "framework": "React",
                        "folders": [
                            "client/src/components",
                            "client/src/pages",
                            "client/src/context"
                        ]
                    }
                elif "flask" in intent or "fastapi" in intent or "python" in intent:
                    architecture["project_type"] = "python_web_app"
                    architecture["backend"] = {
                        "language": "python",
                        "framework": "Flask" if "flask" in intent else "FastAPI",
                        "entry_point": "app.py"
                    }
                else:
                    architecture["frontend"] = {
                        "framework": "HTML/CSS/JS",
                        "folders": ["index.html", "style.css", "script.js"]
                    }
                    architecture["backend"] = {
                        "framework": "Express",
                        "folders": [
                            "server/routes",
                            "server/models",
                            "server/middleware"
                        ]
                    }

                if "database" in intent or "mongo" in intent:
                    architecture["database"] = "MongoDB"
                elif "sqlite" in intent or "sql" in intent:
                    architecture["database"] = "SQLite"

                if "api_routes" not in architecture["features"]:
                    architecture["features"].append("api_routes")

        return architecture

    def _extract_tasks(self, analyzer_result):
        if not analyzer_result:
            return []

        if isinstance(analyzer_result, dict):
            if "tasks" in analyzer_result and isinstance(analyzer_result["tasks"], list):
                return analyzer_result["tasks"]
            raw_output = analyzer_result.get("output", "")
        elif isinstance(analyzer_result, str):
            raw_output = analyzer_result
        else:
            return []

        if not isinstance(raw_output, str) or not raw_output.strip():
            return []

        cleaned = re.sub(r"```json|```", "", raw_output).strip()
        try:
            data = json.loads(cleaned)
            return data.get("tasks", []) if isinstance(data, dict) else []
        except Exception:
            return []
