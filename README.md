# Autoforge AI — Personal Autonomous Engineering & Research Workbench

Welcome to **Autoforge AI** (Personal Edition — Washifur).

Autoforge AI is an autonomous multi-agent software engineering, architectural planning, and research synthesis platform. It includes both a full FastAPI backend pipeline and a classical, restrained light-themed web workbench.

---

## Core Capabilities

- **Classical Professional Workbench UI:** Served directly at `http://localhost:8000/`, featuring a warm alabaster paper surface (`#F6F5F1`), crisp slate borders (`#D5D1C8`), classical serif headings, and a restrained Oxford navy accent (`#1F3A5F`).
- **Autonomous Multi-Agent Pipeline (`AgentController` & `AIEngine`):** Decomposes natural-language specifications into structured tasks, plans software architecture, routes across AI providers (`OpenAI`, `Gemini`, `Claude`, `NVIDIA`), and packages complete deliverables.
- **Resilient Provider & Search Initialization:** Starts cleanly even when `.env` API keys are partially configured, automatically falling back across available LLM providers and heuristic task analysis.
- **Automated Project Validation & Runtime Self-Repair:** `ProjectValidator`, `RuntimeTester`, and `AIRepairAgent` validate generated project structures, execute Python entry points in isolated subprocesses, and autonomously repair runtime tracebacks up to 3 times.
- **Executive PDF Report Generation:** `ResearchAgent`, `ReportBuilderV2`, and `PDFGenerator` synthesize web research and compile clean, downloadable PDF reports.
- **Live Project Preview Server & Deliverable Registry:** Browse generated project folders, download `.zip` packages or `.pdf` reports, and launch local preview servers directly from the UI.

---

## Architecture & Workflow

1. **Web / Application Specification:** Autoforge AI designs the architecture, generates multi-file project code (`src/app.py`, `requirements.txt`, `index.html`, etc.), writes to `generated_projects/`, validates entry points, runs startup tests with self-repair, and packages a downloadable `.zip` archive.
2. **Research / Executive Document Specification:** Autoforge AI gathers web context via `ResearchAgent`, structures an executive report via `ReportBuilderV2`, and compiles a downloadable PDF document (`generated_report.pdf`).
3. **Direct Architectural Consultation:** Interactive stateful chat (`/api/chat`) for rapid technical Q&A and specification refinement.

---

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the Autoforge AI Web Workbench (Light Theme) |
| `GET` | `/api/status` | Returns system health, configured AI providers, and workspace metrics |
| `POST` | `/api/generate` | Runs the full autonomous multi-agent generation pipeline |
| `POST` | `/api/chat` | Stateful conversational endpoint with multi-provider selection |
| `GET` | `/api/projects` | Lists all generated projects, ZIP archives, and PDF reports |
| `GET` | `/api/download?path=...` | Downloads a generated ZIP, PDF, or image artifact |
| `POST` | `/api/preview` | Starts a local preview server for a generated project |
| `POST` | `/api/preview/stop` | Stops an active project preview server |

---

## Quick Start

1. **Configure Environment Variables:**
   Open `.env` in the project root and add one or more provider keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `CLAUDE_API_KEY`, `TAVILY_API_KEY`).

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch Autoforge AI:**
   ```bash
   python api.py
   ```
   Open `http://localhost:8000` in your browser to access the **Autoforge AI Workbench**, or visit `http://localhost:8000/docs` for the interactive OpenAPI documentation.
