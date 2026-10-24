# AgentOps

### A personal project exploring agent architecture with open-weight models

AgentOps is an open-source project I'm building to understand how multi-step AI agents are put together. The core idea is to keep the agent logic independent of the model provider: an adapter layer lets LLaMA 3.2, Mistral 7B, Qwen 2.5 Coder and DeepSeek R1 (via the Hugging Face router) be swapped without changing the rest of the system. OpenAI-compatible and local fallback adapters are included too.

> **Status: early-stage learning project, not a production system.** See [Known Gaps](#known-gaps) before running it anywhere that matters.

---

## Screenshots

**Conversational interface** - dark theme, collapsible session sidebar, quick-prompt chips and a prompt composer.

![AgentOps Conversational Interface](img/output1.png)

**Model adapter selector** - switch between supported open-weight models at runtime.

![Modular Model Selector](img/op2.png)

---

## Design Overview

| Area | What it does |
|---|---|
| **Model adapters** | `ModelAdapterFactory` decouples agent logic from the provider. Hugging Face router, OpenAI-compatible and local fallback adapters. |
| **Memory** | Token-budgeted sliding window for short-term context; local vector store using MiniLM-L6-v2 embeddings with cosine-similarity retrieval. |
| **Tools** | Web search and scraping, HTTP client, SQL queries and a Python execution tool, exposed through a REST API. |
| **Reasoning** | ReAct-style loop; reasoning steps are streamed to the UI over server-sent events (SSE). |
| **Stack** | Next.js 14 frontend, Python backend (Flask and FastAPI), Docker. |

### Architecture

```text
+-----------------------------------------------------------------------------+
|                             Next.js 14 Frontend                             |
|       (Chat UI | Telemetry Dashboard | Workflows | Swarm | Memory | SQL)     |
+--------------------------------------|--------------------------------------+
                                       | Server-Sent Events (SSE) / REST
+--------------------------------------v--------------------------------------+
|                       Python Backend (Flask / FastAPI)                      |
+--------------------------------------+--------------------------------------+
| Modular Model Adapters               | Memory                               |
| - Hugging Face Router                | - Short-Term Sliding Buffer          |
| - OpenAI-Compatible Adapter          | - Vector Store (MiniLM-L6-v2)        |
| - Offline Local Fallback Adapter     | - Relational Conversation Store      |
+--------------------------------------+--------------------------------------+
| Tools                                | Orchestration & Multimodal           |
| - HTTP / REST API Caller             | - Agent Swarm                        |
| - Web Scraper & DuckDuckGo Search    | - Multi-Stage Workflows              |
| - SQL Query & Schema Tool            | - BLIP Vision Analysis               |
| - Python Execution Tool (see gaps)   | - Whisper Speech-to-Text             |
+-----------------------------------------------------------------------------+
```

### Model adapters

- `HuggingFaceAdapter`: Hugging Face router (`https://router.huggingface.co/v1`).
- `OpenAIAdapter`: any OpenAI-compatible endpoint.
- `LocalFallbackAdapter`: self-contained offline engine for running without a token.

Supported models in the selector: LLaMA 3.2 (3B), Mistral 7B, Qwen 2.5 (72B), Qwen 2.5 Coder (32B), DeepSeek R1.

### Tools

- **Web**: scraping and search parsing via BeautifulSoup and DuckDuckGo.
- **HTTP client**: GET, POST, PUT, DELETE with configurable headers and payloads.
- **SQL**: schema inspection and query execution over SQLite and PostgreSQL.
- **Python execution**: runs model-generated scripts. **Not hardened for untrusted input.**

### Memory

- **Short-term**: token-budgeted sliding window.
- **Long-term**: local vector store using `sentence-transformers/all-MiniLM-L6-v2`, cosine-similarity retrieval.

---

## Known Gaps

This is an early-stage project. Things I know are missing or weak:

- **Code execution is not safe for untrusted input.** Do not expose the Python execution tool to untrusted users or networks.
- **No authentication** on the API.
- **No evaluation suite** yet, so agent behaviour and retrieval quality are not measured.
- **The vector store is file-based** (`vector_store.json`), which will not scale and has no concurrency guarantees.

These are what I plan to work on next.

## Feedback Welcome

If you work on agent systems, I'd especially value feedback on:

- **Memory design** (context budgeting, retrieval strategy, what to persist)
- **Safe tool execution** (sandboxing, permissions, limiting blast radius)

Issues and PRs are welcome.

---

## Directory Structure

```text
agentops/
|-- backend/
|   |-- app/
|   |   |-- adapters/         # Model adapters (Hugging Face, OpenAI-compatible, Local)
|   |   |-- agents/           # Multi-agent swarm definitions
|   |   |-- intelligence/     # Prompts, personas, ReAct reasoning engine
|   |   |-- memory/           # Sliding context buffer and vector store
|   |   |-- routes/           # FastAPI routers
|   |   |-- services/         # Master coordinator, voice, vision
|   |   |-- tools/            # Web search, scraper, API caller, DB, code runner
|   |   |-- config.py         # Backend configuration settings
|   |   |-- database.py       # SQLAlchemy engine and session factory
|   |   |-- models.py         # Relational database models
|   |-- app_flask.py          # Flask server with modular adapters
|-- frontend/
|   |-- app/                  # Next.js 14 layout and page routes
|   |-- components/           # UI components (ChatInterface, Composer, Workspace, Sidebar)
|   |-- lib/                  # API client, types, constants
|   |-- styles/               # CSS modules and design tokens
|   |-- package.json          # Node dependencies
|-- img/                      # README screenshots
|-- .env.example              # Environment variables template
|-- docker-compose.yml        # Multi-container orchestration
`-- README.md
```

---

## Quick Start

### 1. Environment

```bash
cp .env.example .env
```

```ini
# Hugging Face access token (optional if using the local fallback)
HF_TOKEN=your_token_here
HF_ROUTER_BASE_URL=https://router.huggingface.co/v1
HF_DEFAULT_MODEL=meta-llama/Llama-3.2-3B-Instruct

# Database and storage
DATABASE_URL=sqlite:///./ai_agent.db
VECTOR_STORE_PATH=./vector_store.json

# Server
HOST=0.0.0.0
PORT=8000
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
python app_flask.py
```

Or run the FastAPI server instead:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

### Docker

```bash
docker-compose up --build
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/send` | Synchronous message with ReAct reasoning and tool calls |
| `POST` | `/api/chat/stream` | SSE stream of tokens and reasoning steps |
| `GET` | `/api/conversations/` | List conversation threads |
| `POST` | `/api/conversations/create` | Create a conversation thread |
| `DELETE` | `/api/conversations/<id>` | Delete a thread and its history |
| `GET` | `/api/tools/` | List registered tools and parameter specs |
| `POST` | `/api/tools/execute` | Invoke a tool directly |
| `GET` | `/api/memory/` | Query vector memory by cosine similarity |
| `POST` | `/api/memory/add` | Add a document to vector memory |
| `POST` | `/api/workflows/execute` | Run a multi-phase workflow |

---

## License

MIT License.
