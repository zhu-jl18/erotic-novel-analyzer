<!-- OPENSPEC:START -->

# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:

- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:

- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# Repository Guidelines

## Git Identity

This repository is owned by **lovingfish**. Before committing or using `gh` CLI, verify your identity:

```bash
# Check current Git identity (repo-level)
git config user.name
git config user.email

# Switch to the correct identity (repo-level only, won't affect global config)
git config --local user.name "lovingfish"
git config --local user.email "nontrivial2025@gmail.com"

# Check GitHub CLI auth status
gh auth status
```

> **Note**: The `--local` flag ensures these settings apply **only to this repository** and won't override your global Git configuration.

Ensure commits are attributed to the correct user to maintain a clean contribution history.

## Project Structure & Module Organization

```
.
├── backend.py                 # FastAPI server (routes + error mapping)
├── src/novel_analyzer/        # LLM client + schemas + config + truncation + logging
├── config/llm.yaml            # Fixed LLM strategy config (read-only path)
├── config/prompts/*.j2        # Prompt templates (Jinja2)
├── templates/index.html       # Single-page UI (Alpine.js) served by FastAPI
├── static/                    # CSS + client-side rendering (e.g., chart-view.js)
│   ├── style.css
│   └── chart-view.js
├── requirements.txt           # Python runtime dependencies
├── requirements-dev.txt       # Development dependencies (Playwright, pytest)
├── .env.example               # Config template (copy to .env; never commit secrets)
├── start.bat                  # Windows launcher (installs deps, starts server)
└── tests/                     # Test suite
    ├── test_export_report_e2e.py
    ├── test_thunderzones_e2e.py
    ├── test_thunderzones.py
    ├── fixtures/
    └── export/
```

Keep changes cohesive: routing in `backend.py`, LLM/validation/config in `src/novel_analyzer/`, UI state/behavior in `templates/index.html`, reusable JS rendering helpers in `static/`.

## Build, Test, and Development Commands

### Setup

- **Required**: Create venv: `python -m venv venv`
- **Required**: Always run commands via the venv interpreter (either activate it or call it explicitly)
  - Activate (Windows): `.\venv\Scripts\activate`
  - Explicit (Windows): `.\venv\Scripts\python.exe ...`
- Install deps: `.\venv\Scripts\python.exe -m pip install -r requirements.txt`
- Install dev deps: `.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt`

### Testing

- Run all unit tests: `.\venv\Scripts\python.exe -m pytest -q`
- Run all E2E tests: `.\venv\Scripts\python.exe -m pytest tests/test_*_e2e.py -q`
- Run specific test file: `.\venv\Scripts\python.exe -m pytest tests/test_thunderzones.py -q`
- Run with verbose output: `.\venv\Scripts\python.exe -m pytest -v`

### E2E Test Setup

```bash
# Install Playwright
.\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\venv\Scripts\python.exe -m playwright install chromium
```

## Coding Style & Naming Conventions

### Python

- 4-space indentation
- Keep functions small and focused
- Validate external inputs (paths, URLs, LLM output)
- Prefer type hints for public helpers and request/response models
- Internal helpers use a leading `_` (e.g., `_validate_api_url`, `_raise_errors`)

### Frontend

- Stay "vanilla" (Alpine.js + DOM APIs)
- Avoid adding build tooling unless there's a strong reason
- Follow existing patterns in `templates/index.html` and `static/chart-view.js`

### API Design

- Endpoints live under `/api/*`
- Use Pydantic models for request/response validation
- Return proper HTTP status codes (400 for client errors, 422 for validation errors, 500 for server errors)

## Testing Guidelines

### Test Files

- `test_thunderzones.py` - Unit tests for thunderzone detection logic
- `test_export_report_e2e.py` - E2E test for export report functionality
- `test_thunderzones_e2e.py` - E2E test for thunderzone UI and detection

### Test Requirements

Before opening a PR, ensure:

1. **Syntax Check**

   ```bash
   .\venv\Scripts\python.exe -m compileall backend.py src/novel_analyzer
   ```

2. **Unit Tests**

   ```bash
   .\venv\Scripts\python.exe -m pytest -q
   ```

   All tests must pass.

3. **E2E Tests**

   ```bash
   .\venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   .\venv\Scripts\python.exe -m playwright install chromium
   .\venv\Scripts\python.exe -m pytest -q
   ```

   All E2E tests must pass.

4. **Manual Smoke Test**
   - Start the server
   - Select a small `.txt` novel
   - Run analysis
   - Verify key tabs render (summary, characters, relationships, thunderzones)
   - Test export functionality
   - Test log system

### Test Coverage Goals

- Core backend logic (validation, reconciliation)
- Frontend rendering functions (export, visualization)
- API endpoints
- E2E workflows

## Commit & Pull Request Guidelines

### Commit Messages

Follow Conventional Commits observed in history:

- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `docs:` - Documentation changes
- `test:` - Test changes
- `chore:` - Maintenance tasks

Use short summaries in Chinese or English.

### Pull Requests

PRs should include:

- **What changed**: Clear description of the changes
- **Why**: Motivation or problem being solved
- **How to verify**: Steps to test the changes
- **Screenshots/GIFs**: For UI changes

### Security Considerations

- Call out security-impacting edits explicitly (path handling, host binding, file access)
- Backward compatibility is not required—prefer clarity over preserving old behavior
- Never commit `.env` or API keys

## Security & Configuration Tips

### Configuration

- Keep `HOST=127.0.0.1` unless you intentionally want LAN exposure
- Never commit `.env` or API keys to the repository
- Keep novel files local and treat them as sensitive input
- Use `LOG_LEVEL=warning` in production to reduce noise

### Security Headers

The server includes security middleware:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `X-Frame-Options: DENY`

### Path Security

- Backend does not scan/read local novel files (no directory traversal surface)
- Novel content is imported on the frontend via local file selection (single `.txt`)

### LLM Security

- API keys are only stored on the server (`.env`)
- Frontend never has access to API keys
- LLM responses are validated and sanitized before use
- `LLM_DUMP_ENABLED=false` in production to prevent leaking raw LLM responses

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run unit tests: `.\venv\Scripts\python.exe -m pytest -q`
4. Run E2E tests: `.\venv\Scripts\python.exe -m pytest tests/test_*_e2e.py -q`
5. Manually smoke test the UI
6. Commit with conventional commit message
7. Push and create a PR
8. Ensure all CI checks pass

## Common Issues

### Import Errors

- Ensure you're using a virtual environment
- Run `.\venv\Scripts\python.exe -m pip install -r requirements.txt`

### Playwright Issues

- Run `.\venv\Scripts\python.exe -m playwright install chromium`
- Ensure Chromium browser is installed

### Port Already in Use

- Change `PORT` in `.env` or
- Kill the process using port 6103: `netstat -ano | findstr :6103` (Windows)

### API Connection Failures

- Check `API_BASE_URL`, `API_KEY`, `MODEL_NAME` in `.env`
- Test connection via `/api/test-connection` endpoint
- Check firewall/network settings
