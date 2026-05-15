# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
# Install dependencies (first time)
uv sync

# Start the server (from project root)
./run.sh

# Or manually
cd backend && uv run uvicorn app:app --reload --port 8000
```

App runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

Requires `ANTHROPIC_API_KEY` in a `.env` file at the project root.

On startup, FastAPI loads all `.txt`/`.pdf`/`.docx` files from `../docs` into ChromaDB, skipping any courses already indexed.

## Architecture

This is a RAG chatbot where users ask questions about course documents. The backend is FastAPI + ChromaDB + Claude; the frontend is vanilla JS.

### Query Flow

1. **Frontend** (`frontend/script.js`) POSTs `{ query, session_id }` to `/api/query`
2. **`app.py`** creates a session if none exists, delegates to `RAGSystem.query()`
3. **`rag_system.py`** fetches conversation history, calls `AIGenerator.generate_response()` with the `search_course_content` tool available, then saves the exchange to session history
4. **`ai_generator.py`** makes **API call #1** to Claude with `tool_choice: auto`. If Claude invokes the tool (`stop_reason == "tool_use"`), `_handle_tool_execution()` runs it and makes **API call #2** for synthesis. Otherwise returns the direct answer.
5. **`search_tools.py`** → **`vector_store.py`**: `CourseSearchTool` calls `VectorStore.search()`, which does a semantic match on `course_catalog` to resolve the course name, then queries `course_content` chunks (top 5) with optional course/lesson filters. Source labels are stored on the tool instance and retrieved by `ToolManager` after each query.

### Key Design Decisions

- Claude makes **1 API call** for general knowledge questions, **2** for course-specific ones (routing + synthesis).
- Conversation history is passed as a **flat string appended to the system prompt**, not as proper `messages` entries. Capped at 2 exchanges (`MAX_HISTORY` in config).
- ChromaDB uses **two collections**: `course_catalog` (course-level metadata for name resolution) and `course_content` (800-char chunks with 100-char overlap).
- Tool sources (`CourseSearchTool.last_sources`) are **instance state** reset after each query — not thread-safe if concurrency is added.
- Documents are chunked and embedded using `sentence-transformers/all-MiniLM-L6-v2` locally; no external embedding API.

### Adding a New Tool

1. Create a class extending `Tool` (ABC in `search_tools.py`) implementing `get_tool_definition()` and `execute()`
2. Register it: `tool_manager.register_tool(your_tool)` in `RAGSystem.__init__()`

### Adding a New Document Type

Extend `DocumentProcessor.process_course_document()` in `document_processor.py` — currently handles `.pdf`, `.docx`, `.txt`.
