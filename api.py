import os
import httpx
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response, RedirectResponse
from pydantic import BaseModel
from ai_engine.core.ai_engine import AIEngine
from ai_engine.preview.preview_agent import PreviewAgent
from ai_engine.providers.provider_factory import ProviderFactory


app = FastAPI(
    title="Autoforge AI — Personal Autonomous Engineering & Research Workbench",
    description="Personal multi-agent AI engineering, research synthesis, and project generation system for Washifur.",
    version="2.0.0"
)

# Ensure directories exist
Path("generated_projects").mkdir(parents=True, exist_ok=True)
Path("frontend").mkdir(parents=True, exist_ok=True)

# Mount static assets
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize the AI Engine & Preview Agent
engine = AIEngine()
preview_agent = PreviewAgent()

# In-memory storage for chat sessions and task history
chat_sessions = {}
execution_history = []


class GenerateRequest(BaseModel):
    prompt: str


class ChatRequest(BaseModel):
    prompt: str
    session_id: str = "default"
    provider: str = "gemini"


class PreviewRequest(BaseModel):
    project_path: str


@app.get("/")
def serve_workbench():
    index_file = Path("frontend/index.html")
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "Autoforge AI Server is running. Visit /docs to test endpoints."}


@app.get("/api/status")
def get_system_status():
    """
    Returns system status, configured providers, and workspace summary for Autoforge AI.
    """
    providers = ProviderFactory.get_provider_status()
    tavily_configured = bool(os.getenv("TAVILY_API_KEY"))

    projects = _scan_generated_artifacts()

    return {
        "system": "Autoforge AI",
        "edition": "Personal Edition — Washifur",
        "version": "2.0.0",
        "status": "operational",
        "providers": providers,
        "web_search": tavily_configured,
        "artifact_count": len(projects),
        "active_previews": list(preview_agent.active_processes.keys()),
    }


@app.get("/api/projects")
def list_generated_projects():
    """
    Lists all generated project directories, ZIP archives, PDF reports, and images.
    """
    return {
        "status": "success",
        "artifacts": _scan_generated_artifacts(),
        "history": execution_history[:25],
    }


@app.get("/api/download")
def download_artifact(path: str):
    """
    Safely downloads a generated ZIP, PDF, or image inside generated_projects.
    """
    base_dir = Path("generated_projects").resolve()
    target = Path(path).resolve()

    if not str(target).startswith(str(base_dir)) or not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found or access denied.")

    return FileResponse(
        path=str(target),
        filename=target.name,
        media_type="application/octet-stream"
    )


@app.post("/api/generate")
def generate_project(req: GenerateRequest):
    """
    Takes a text prompt and runs the full Autoforge AI multi-agent pipeline
    (Task Analysis -> Architecture Planning -> Multi-Provider Execution -> Validation & Self-Repair / PDF Export).
    """
    print(f"\n[AUTOFORGE AI] Received generation prompt: {req.prompt}\n")

    try:
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = engine.run(req.prompt)

        # Record in history
        execution_history.insert(0, {
            "timestamp": started_at,
            "prompt": req.prompt,
            "result": result
        })

        return {
            "status": "success",
            "message": "Autoforge AI pipeline execution completed.",
            "data": result
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preview")
def preview_project(req: PreviewRequest):
    return preview_agent.start_preview(req.project_path)


@app.post("/api/preview/stop")
def stop_preview_project(req: PreviewRequest):
    return preview_agent.stop_preview(req.project_path)


@app.get("/preview/{project_name}")
def redirect_preview_root(project_name: str):
    return RedirectResponse(url=f"/preview/{project_name}/")


@app.api_route("/preview/{project_name}/{subpath:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_preview_request(project_name: str, subpath: str, request: Request):
    """
    Reverse-proxies preview requests through the main FastAPI server port so
    previews work seamlessly on Render and cloud hosts (which only expose one port).
    Also supports direct static file serving if no subprocess is needed.
    """
    project_dir = (Path("generated_projects") / project_name).resolve()
    base_dir = Path("generated_projects").resolve()

    if not str(project_dir).startswith(str(base_dir)) or not project_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    # Ensure preview server is started if not already active
    active_info = preview_agent.active_processes.get(str(project_dir))
    if not active_info or active_info["process"].poll() is not None:
        start_res = preview_agent.start_preview(str(project_dir))
        active_info = preview_agent.active_processes.get(str(project_dir))
        if not active_info:
            # Fallback: serve static HTML/CSS/JS files directly from project_dir or project_dir/public
            return _serve_static_fallback(project_dir, subpath)

    port = active_info["port"]
    target_url = f"http://127.0.0.1:{port}/{subpath}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    try:
        body = await request.body()
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

        excluded_headers = {"content-encoding", "transfer-encoding", "content-length", "connection"}
        response_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in excluded_headers
        }
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type"),
        )
    except Exception:
        return _serve_static_fallback(project_dir, subpath)


def _serve_static_fallback(project_dir: Path, subpath: str):
    rel = subpath.strip("/") or "index.html"
    for candidate_root in (project_dir, project_dir / "public", project_dir / "frontend", project_dir / "src"):
        candidate = (candidate_root / rel).resolve()
        if str(candidate).startswith(str(project_dir)) and candidate.exists() and candidate.is_file():
            return FileResponse(str(candidate))
    raise HTTPException(status_code=404, detail=f"Preview resource '{rel}' not found.")


@app.get("/api/debug-path")
def debug_path():
    return {
        "cwd": os.getcwd(),
        "exists_ai_engine": Path("ai_engine").exists(),
        "generated_projects": [
            str(p) for p in Path("generated_projects").iterdir()
        ] if Path("generated_projects").exists() else []
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """
    Fast, conversational endpoint that maintains session history and falls back gracefully.
    """
    print(f"\n[AUTOFORGE CHAT] Session: {req.session_id} | Prompt: {req.prompt}\n")

    try:
        if req.session_id not in chat_sessions:
            chat_sessions[req.session_id] = [
                {
                    "role": "system",
                    "content": (
                        "You are Autoforge AI, a refined, articulate personal AI software architect "
                        "and research assistant created for Washifur. Provide clear, structured, "
                        "and technically rigorous responses."
                    )
                }
            ]

        chat_sessions[req.session_id].append({"role": "user", "content": req.prompt})

        chat_provider = ProviderFactory.get_provider(req.provider or "gemini")

        if hasattr(chat_provider, "generate_chat_response"):
            result = chat_provider.generate_chat_response(chat_sessions[req.session_id])
        else:
            result = chat_provider.generate_response(req.prompt)

        if result.get("status") == "success":
            output_text = result.get("output", "")
            chat_sessions[req.session_id].append({"role": "assistant", "content": output_text})

            return {
                "status": "success",
                "message": "Chat response generated.",
                "data": {
                    "response": output_text,
                    "provider": result.get("provider", req.provider),
                    "session_id": req.session_id
                }
            }
        else:
            # Helpful fallback message when no API keys are configured in .env yet
            fallback_msg = (
                f"[Notice: {result.get('output', 'Provider unavailable')}]\n\n"
                "Autoforge AI is online and ready, but no active LLM API key replied. "
                "Add at least one key (`MISTRAL_API_KEY`, `GROK_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, or `NVIDIA_API_KEY`) to your `.env` file."
            )
            return {
                "status": "warning",
                "message": "Provider key not configured.",
                "data": {
                    "response": fallback_msg,
                    "provider": "system",
                    "session_id": req.session_id
                }
            }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _scan_generated_artifacts():
    base = Path("generated_projects")
    if not base.exists():
        return []

    items = []
    for entry in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if entry.name.startswith("."):
            continue
        stat = entry.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        if entry.is_dir():
            file_count = sum(1 for _ in entry.rglob("*") if _.is_file())
            zip_candidate = base / f"{entry.name}.zip"
            items.append({
                "name": entry.name,
                "kind": "project_dir",
                "path": str(entry),
                "zip_path": str(zip_candidate) if zip_candidate.exists() else None,
                "file_count": file_count,
                "modified": mtime,
            })
        elif entry.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"}:
            items.append({
                "name": entry.name,
                "kind": entry.suffix.lower().lstrip("."),
                "path": str(entry),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": mtime,
            })
    return items


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, reload_excludes=["generated_projects"])
