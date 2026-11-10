# Autoforge AI

Multi-agent backend engine and web interface for generating project boilerplates, running automation scripts, and compiling PDF research reports from text prompts.

Built with FastAPI, Python, and a lightweight vanilla JS frontend.

## Overview

Autoforge AI takes a prompt, breaks it down into tasks, plans the folder structure, and routes the generation step across whatever LLM provider keys are available in `.env`.

Once code is generated, the backend writes the files to `generated_projects/`, validates the structure, runs a quick startup check (with up to 3 automatic repair attempts if a Python script crashes), and packages everything into a `.zip` file. It also includes a local preview runner (`PreviewAgent`) that spins up generated Node/Express, static HTML, or Python projects on a free localhost port.

### Key Features

- **Multi-provider routing & failover:** Supports Gemini (default primary), Groq / Grok (xAI), Mistral, OpenAI, Claude, and NVIDIA NIM. You only need one API key configured—if a provider isn't set or fails to respond, `ProviderFactory` falls back to the next available key automatically.
- **Project generation & packaging:** Parses multi-file outputs into `generated_projects/<project_name>` and creates a downloadable `.zip` archive.
- **Validation & self-repair:** `ProjectValidator` and `RuntimeTester` check entry points (`app.py`, `main.py`, `server.js`, `index.html`) and feed runtime tracebacks to `AIRepairAgent` to patch broken imports or syntax errors.
- **Live preview server:** Starts and stops local preview servers for generated Node.js (`npm run start`), static HTML, or Python apps directly from the UI.
- **PDF report pipeline:** Uses Tavily web search (when configured) and `fpdf` / `reportlab` to compile research prompts into downloadable PDF files.
- **Web interface:** Served at `/` with three views: Pipeline runner, direct chat, and an archive list of generated projects.

## Project Structure

```text
autoforge-ai/
├── api.py                  # FastAPI server and API routes
├── frontend/               # Web UI (index.html, styles.css, app.js)
├── ai_engine/
│   ├── core/               # Main AIEngine pipeline and ExecutionManager
│   ├── analyzer/           # Prompt task decomposition
│   ├── planner/            # Architecture and task graph planners
│   ├── router/             # Task-to-provider routing logic
│   ├── providers/          # Gemini, Grok/Groq, Mistral, OpenAI, Claude, NVIDIA clients
│   ├── project_builder/    # File parser and ZIP packager
│   ├── validator/          # Project structure checks
│   ├── repair/             # Subprocess runtime tester and repair agent
│   ├── preview/            # Local preview server manager
│   └── document_processing/# PDF reader, chunker, and report generator
├── templates/              # Base project structure metadata
├── tests/                  # Pipeline and component tests
├── start.sh                # Helper script to create .venv and run the server
└── stop.sh                 # Helper script to stop the server on port 8000
```

## Setup & Usage

### 1. Environment Variables

Copy `.env.example` to `.env` (or edit `.env` directly) and add at least one provider API key:

```env
GEMINI_API_KEY=your_key_here
GROK_API_KEY=
MISTRAL_API_KEY=
OPENAI_API_KEY=
CLAUDE_API_KEY=
NVIDIA_API_KEY=

# Optional for web research
TAVILY_API_KEY=
```

### 2. Start the Server

You can use the included shell script, which sets up `.venv` if needed and starts Uvicorn on port `8000`:

```bash
./start.sh
```

Or run it manually:

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python api.py
```

To stop the server: press `Ctrl + C` in the terminal, or run `./stop.sh`.

### 3. Using the App

- **Web UI:** Open `http://localhost:8000`
- **Swagger / API Docs:** Open `http://localhost:8000/docs`

## API Endpoints

- `GET /` — Web interface
- `GET /api/status` — Active provider status and workspace counts
- `POST /api/generate` — Run the full generation pipeline (`{"prompt": "..."}`)
- `POST /api/chat` — Conversational chat endpoint (`{"prompt": "...", "session_id": "...", "provider": "gemini"}`)
- `GET /api/projects` — List generated projects, ZIPs, and PDFs in `generated_projects/`
- `GET /api/download?path=...` — Download a generated `.zip` or `.pdf`
- `POST /api/preview` — Start a local preview server (`{"project_path": "..."}`)
- `POST /api/preview/stop` — Stop a running preview server (`{"project_path": "..."}`)
