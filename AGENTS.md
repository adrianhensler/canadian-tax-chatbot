# Repository Guidelines

## Project Structure & Module Organization

- `src/`: core library code. Key packages include `src/chat/`, `src/retrieval/`, and `src/loaders/`.
- `scripts/`: runnable utilities such as `scripts/ingest_corpus.py`, `scripts/cli.py`, and evaluation helpers.
- `tests/`: pytest suite (e.g., `tests/test_chatbot.py`) plus fixtures in `tests/fixtures/`.
- `docs/`: architecture, PRD, and ingestion specifications.
- `data/` and `eval/`: corpus artifacts and evaluation dataset (`eval/README.md`).

## Build, Test, and Development Commands

- `python3 -m venv venv && source venv/bin/activate`: create/activate virtualenv.
- `pip install -e .`: install editable package with runtime deps.
- `python scripts/ingest_corpus.py --download`: download and ingest the Income Tax Act XML corpus.
- `python scripts/cli.py --help`: show CLI usage; `python scripts/cli.py "Question?"` runs a single query.
- `pytest tests/ -v`: run the test suite (uses `pytest.ini` + `pyproject.toml` options).
- `OPENAI_API_KEY=sk-... python scripts/evaluate_chatbot.py`: run eval dataset scoring.

## Coding Style & Naming Conventions

- Python 3.10+ with full type hints (see `pyproject.toml`).
- Formatting: `black` (line length 100). Linting: `ruff`. Type checking: `mypy`.
- Naming: modules and functions in `snake_case`, classes in `PascalCase`.
- Tests follow `test_*.py`, classes `Test*`, functions `test_*`.

## Testing Guidelines

- Framework: `pytest` with coverage via `pytest-cov` (`--cov=src --cov-report=term-missing`).
- Add tests alongside new features in `tests/`; use fixtures in `tests/fixtures/`.
- Prefer targeted test runs during development, e.g. `pytest tests/test_retriever.py -v`.

## Commit & Pull Request Guidelines

- Commit messages are imperative, sentence-case, and short (e.g., “Implement Phase 3: CLI Interface”).
- PRs should include: a concise description, linked issue (if any), and test evidence (commands + results).
- Include screenshots for UI changes; note any data downloads or schema changes.

## Configuration & Secrets

- Set `OPENAI_API_KEY` for LLM-backed features and evaluation scripts.
- Do not commit corpus downloads or generated embeddings under `data/`.

## Agent-Specific Instructions

- Check `docs/architecture.md` and `docs/ingestion-spec.md` before changing ingestion or retrieval logic.
- `CLAUDE.md` contains historical guidance; treat it as supplemental if it conflicts with current code or README.
