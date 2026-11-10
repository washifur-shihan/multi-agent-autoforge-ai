import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()


class WebSearchTool:
    """
    Web search tool using Tavily API for Autoforge AI.
    Gracefully handles missing API keys without crashing initialization.
    """

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.client)

    def search(self, query):
        if not self.is_configured:
            return {
                "status": "skipped",
                "error": "TAVILY_API_KEY not configured in .env",
                "result": []
            }

        try:
            response = self.client.search(
                query=query,
                search_depth="basic",
                max_results=5
            )

            results = []

            for r in response.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")
                })

            return {
                "status": "success",
                "result": results
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "result": []
            }
