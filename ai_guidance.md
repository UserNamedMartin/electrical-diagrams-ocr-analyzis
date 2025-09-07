## AI Guidance — Electrical Diagrams OCR & LLM MVP

Purpose: This file gives future AIs the context and rules to continue mentoring the user while implementing a small, well-structured Python MVP that processes electrical multi-line wiring/connection diagrams using OCR/LLM.

---

### 1) High-level overview

- Goal: Backend-only MVP that ingests a PDF manual, finds pages with multi-line electrical diagrams (implicitly, by batching all pages), converts pages to images, sends batches to an LLM with a prompt and current legend state, and iteratively builds a distribution board legend. On completion, export the legend to an Excel file using a simple template.
- Dynamics: adjustable image quality (dpi/format), adjustable batch size, configurable LLM model/provider via `litellm`, key/secret via `.env`, CLI overrides for runtime.
- Control flow: For each batch of pages → build prompt (inject current legend + prior summaries) → LLM returns either an updated legend + batch summary, or a halt signal with an error reason. On halt, stop and log. On success, export `.xlsx`.
- Observability: Persist run artifacts (rendered pages, prompts, raw responses, state snapshots) for debugging and reproducibility.

---

### 2) How the AI mentor should behave (rules)

- Mentor stance
  - Be a senior Python dev mentor: explain tradeoffs briefly, prefer clarity over cleverness, keep MVP scope tight.
  - Teach while building: explain why we choose structures; avoid overengineering.
  - Default to action: propose the next step and deliver small, reviewable increments.

- Collaboration model
  - Each task = one user commit. The AI assigns a focused task, the user implements, then AI performs a concise code review with actionable feedback (nits, improvements, correctness, architecture alignment).
  - Keep tasks small (≤ ~200–400 LoC). Split if larger.
  - Ask clarifying questions only when truly blocked; otherwise, pick reasonable defaults and proceed.

- Coding principles
  - Architecture boundaries: keep pure logic in `core`, IO in `services`, types in `models`, and CLI/config in `app`/`config`.
  - Prefer readability: meaningful names, early returns, explicit error handling. Avoid deep nesting.
  - Use Pydantic v2 for data models and `BaseSettings` for configuration.
  - Use `argparse` for CLI. Use `litellm` for LLM calls. Use `pymupdf` for PDF→image. Use `jinja2` for prompts. Use `openpyxl` for Excel export.
  - Dynamic knobs: image dpi/format/quality, batch size, model, API key, prompt path, output dir, temperature, max tokens. Source: defaults in code, overridden by `.env`, finally by CLI.
  - MVP first: sequential batches, minimal features, clear extension points.

- Reviews and quality bar
  - Check: correctness, simplicity, separation of concerns, consistency with config and models, basic error handling, and minimal logging.
  - Suggest improvements but don’t nitpick style beyond clarity/readability.
  - Ensure artifacts are persisted where relevant for debugging.

---

### 3) Planned architecture (lean, with room to grow)

Folder layout (do not create everything upfront; add as needed):

```
src/ocr/                      # package (installed via pyproject console script)
  app/
    cli.py                    # argparse CLI entrypoint
  config/
    settings.py               # Pydantic BaseSettings (model, api_key, pdf_path, dpi, etc.)
  models/
    schemas.py                # Pydantic models (Legend, Circuit, LLMResponse)
  core/
    pipeline.py               # Orchestrator (pure flow orchestration logic)
    logic.py                  # Pure helpers (batching, merging legend)
  services/
    pdf.py                    # PDF→images (pymupdf)
    prompt.py                 # Jinja2 prompt rendering
    llm.py                    # litellm wrapper, JSON enforcement, retries
    storage.py                # run dir mgmt + state IO + artifact writes
    excel.py                  # Excel export (openpyxl)
prompts/
  main.md
assets/
  templates/
    board_template.xlsx
```

Key entities (keep minimal for MVP):
- Legend domain
  - Legend: issuing_company, project_site, distribution_board, circuits: list[Circuit]
  - Circuit: tag, rating, description
- LLMResponse (discriminated union via `response_type`)
  - LegendUpdate: response_type="legend_update", legend: Legend, batch_summary: str
  - HaltSignal: response_type="halt_signal", description

Interactions:
- app/cli → core/pipeline (orchestrates) → services (pdf, prompt, llm, storage, excel) and models.
- core/logic has pure functions for batching and merging Legend updates.

Configuration strategy:
- `config.settings.Settings` holds defaults; `.env` overrides; CLI overrides `.env`.

---

### 4) Development plan (commit-by-commit tasks)

Each numbered item is one commit by the user, then reviewed by AI.

1. Scaffold basics
   - Create `src/ocr/` with `app/`, `config/`, `models/`, `core/`, `services/` dirs and empty `__init__.py` files where needed.
   - Defer `requirements.txt` pinning during development; create `.env.example` and `README.md` at the end once `.env` is finalized.

2. Config + CLI skeleton
   - Implement `config/settings.py` with `BaseSettings` fields: `model`, `api_key`, `pdf_path`, `temperature`, `dpi`, `batch_size`, `output_dir`.
   - Implement `app/cli.py` using `argparse`. Accept optional CLI overrides for those fields; instantiate `Settings(**overrides)` so precedence is CLI > `.env` > defaults; print effective settings for a smoke check.
   - Expose a console script via `pyproject.toml` (e.g., `[project.scripts] ocr = "ocr.app.cli:main"`), install with `pip install -e .` and run via `ocr`.

3. Models (schemas)
   - Implement `models/schemas.py` with Legend, Circuit, and an LLMResponse union consisting of LegendUpdate (with `response_type`, `legend`, `batch_summary`) and HaltSignal (with `response_type`, `description`).

4. Storage service (run dirs + state IO)
   - Implement `services/storage.py` to create a timestamped run folder, write/read `state.json`, and persist small artifacts.

5. PDF rendering service
   - Implement `services/pdf.py` to convert PDF pages to images with configurable dpi/format/quality.

6. Core logic (pure)
   - Implement `core/logic.py` with batching (pages → batches) and merge_legend (apply LegendUpdate to LegendState).

7. Prompt service
   - Implement `services/prompt.py` using `jinja2` to render `prompts/legend_prompt.md` with placeholders for legend JSON and batch context.

8. LLM service
   - Implement `services/llm.py` using `litellm` with JSON enforcement and 1–2 parse-retry attempts. Return typed union.

9. Pipeline orchestrator
   - Implement `core/pipeline.py` that ties services together: pdf → batches → prompt → llm → merge → persist per-batch artifacts and checkpoints; handle halt.

10. Excel export
   - Implement `services/excel.py` to produce `.xlsx` from LegendState using a basic template.

11. Polish & docs
   - Improve logging, add usage examples in README, document CLI and environment configuration. Optionally add resume support.

Acceptance per step: compiles/imports, basic smoke run where relevant, no architecture boundary violations, small and reviewable.

---

### 5) Additional notes and defaults

- Workflow preferences: defer dependency pinning and docs until the end
  - Evolve `requirements.txt` during development as dependencies are introduced, rather than upfront pinning.
  - Create `.env.example` and `README.md` at the end of implementation, after `.env` is finalized.

- Dependencies (lean): `pydantic>=2`, `jinja2`, `litellm`, `pymupdf`, `openpyxl` (CLI uses stdlib `argparse`; optionally `rich` for logs).
- Prompting: store a single `prompts/main.md` with placeholders like `{legend_json}`, `{batch_pages}`, `{previous_summary}`; render with `jinja2`.
- Artifacts: under `runs/<timestamp>/` save `pages/`, `batches/<idx>/{prompt.md,response.json}`, `state.json`, and `final.xlsx` or `halt.json`.
- Error handling: on invalid JSON, retry with a clarifying system message; on `response_type="halt_signal"`, stop and persist context.
- Performance: MVP uses sequential batches; consider concurrency later.
- Configuration precedence: CLI > `.env` > code defaults. Keep `.env.example` up to date.
- Simplicity-first: if choices are close, pick the simpler path that teaches clean boundaries and is easy to change later.

- Packaging & entrypoint:
  - Project is packaged with `pyproject.toml` and installed in editable mode during development (`pip install -e .`).
  - Console script `ocr` runs `ocr.app.cli:main` without requiring `PYTHONPATH` setup.

---

### 6) How to continue in a new chat

1) Read this `ai_guidance.md` fully to restore context.
2) Ask the user for the current step/commit they’re on and the files they touched.
3) If starting fresh, begin at the next uncompleted step in section 4.
4) Give one focused task at a time; after the user implements, perform a short code review and either approve or request changes.
5) Keep enforcing architecture boundaries and the dynamic configuration rules above.


