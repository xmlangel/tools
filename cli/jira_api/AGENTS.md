# Repository Guidelines

## Project Structure & Module Organization
- `create_page.py` is the main script. It contains configuration loading, Confluence client setup, page generation, and CLI entrypoint logic.
- `requirements.txt` lists Python dependencies (e.g., `python-dotenv`, `atlassian-python-api`).
- `confluence_venv/` is a local virtual environment (do not commit).
- `README.md` documents setup and usage.

## Build, Test, and Development Commands
- `python -m venv confluence_venv` creates a local virtual environment.
- `source confluence_venv/bin/activate` (macOS/Linux) activates the venv.
- `pip install -r requirements.txt` installs dependencies.
- `python create_page.py` creates a new page at the space root.
- `python create_page.py <parent_page_id>` creates a page under a parent.

## Coding Style & Naming Conventions
- Python, 4-space indentation, UTF-8 source.
- Use `snake_case` for functions/variables and `PascalCase` for classes.
- Prefer dataclasses for structured data (`Config`, `PageCreationResult`).
- Keep functions small and focused; raise typed exceptions (`ConfigurationError`, `PageCreationError`) for predictable failures.

## Testing Guidelines
- No test framework is currently configured.
- If adding tests, prefer `pytest` and place tests in `tests/` with `test_*.py` naming.
- Example command (after adding pytest): `pytest`.

## Commit & Pull Request Guidelines
- Git history is not available in this directory, so no commit message convention could be inferred.
- Suggested default: short, imperative subject line (e.g., "Add Confluence page body template").
- PRs should include:
  - A concise description of changes and rationale.
  - Any required environment changes (e.g., new `.env` keys).
  - Manual test notes (e.g., "Ran `python create_page.py` against staging space").

## Security & Configuration Tips
- Do not commit `.env` or API tokens.
- Keep `CONFLUENCE_API_TOKEN` scoped to least privilege.
- Avoid logging secrets; log only URLs, space keys, and page IDs.

## Agent-Specific Instructions
- All assistant responses should be written in Korean.
