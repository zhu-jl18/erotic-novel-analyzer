# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Start server (Windows)
start.bat

# Start server (manual)
python backend.py

# Install dependencies
pip install -r requirements.txt
```

Server runs at `http://127.0.0.1:6103` by default.

## Architecture

Single-page app with FastAPI backend + vanilla JS frontend.

```
backend.py          # FastAPI server, LLM API calls, file scanning
templates/
  index.html        # Alpine.js app, all UI state/logic
static/
  style.css         # Tailwind/DaisyUI supplements, shadcn-style components
  chart-view.js     # SVG relationship graph, data rendering functions
```

### Data Flow
1. `scanNovels()` → `GET /api/novels` → renders dropdown
2. `selectNovel()` → `GET /api/novel/{path}` → loads content
3. `analyzeNovel()` → `POST /api/analyze` → LLM analysis → `renderAllData()`

### Frontend Patterns
- Alpine.js `x-data="app()"` manages all state
- DOM rendering via `document.createElement()` (no virtual DOM)
- CSS uses oklch color space with DaisyUI theme variables (`--b1`, `--bc`, `--p`, etc.)

### Backend Patterns
- Config from `.env` via `python-dotenv`
- Path traversal protection in `_safe_novel_path()`
- LLM response JSON extraction handles markdown code blocks

## Configuration

All config in `.env` (copy from `.env.example`):
- `NOVEL_PATH` - novel directory to scan
- `API_BASE_URL`, `API_KEY`, `MODEL_NAME` - OpenAI-compatible API
- `HOST`, `PORT` - server binding
