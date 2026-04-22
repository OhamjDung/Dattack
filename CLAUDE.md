# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Dattack — Human-in-the-Loop AI Data Consultant. User provides a CSV + goal. The system builds a live React Flow node map, runs a deterministic script pipeline against the data, then Gemini synthesises findings via SSE streaming and animates finding nodes onto the map.

## Dev Commands

**Backend** (run from `backend/`):
```bash
uvicorn main:app --reload
```
Runs at `http://localhost:8000`. Requires `GEMINI_API_KEY` in a `.env` file.

**Frontend** (run from `frontend/`):
```bash
npm run dev      # dev server at localhost:5173
npm run build    # tsc -b && vite build
npm run lint     # eslint
```

**Install backend deps:**
```bash
pip install -r backend/requirements.txt
```

## Architecture

### Phase State Machine (frontend)
`App.tsx` owns phase: `context → map → analysis → viz`. Single source of truth for `graphState` (nodes + edges), `streamLog`, and `sessionId`.

### API Flow
1. `POST /context` (multipart/form-data with optional CSV file) → initial node map + `pending_session_id`
2. `POST /research` → add discovered data source/technique/question nodes
3. `POST /feedback` → update nodes based on user feedback on a specific node
4. `POST /approve` → locks map, triggers pipeline, returns `session_id`
5. `GET /stream?session_id=...` → SSE stream of pipeline + synthesis events

Session state (CSV bytes, goal, target_col) lives in `services/session_store.py` — in-memory dict keyed by `session_id`.

### Analysis Pipeline (`backend/analysis/`)
Two-phase pipeline in `runner.py`:

**Phase 1 — Foundation (always runs):**
- `schema_detector` → populates `AnalysisContext.schema`, column type lists
- `field_profile` → populates `ctx.profile`
- `data_quality_report` → populates `ctx.quality`

**Phase 2 — Module selection + execution:**
- Gemini (`select_modules`) picks up to 4 modules from: `exploratory`, `time_series`, `ranking`, `business`, `text`, `anomaly`
- Scripts within a module run in topological waves (parallel within each wave) via `ThreadPoolExecutor`
- Each script module must implement: `DEPENDENCIES: list[str]`, `is_applicable(ctx) -> bool`, `run(ctx) -> dict`
- Script `run()` returns `{"status": "ok"|"skipped"|"error", "findings": [...], "data": {...}}`

**Phase 3 — Synthesis:**
`gemini_service.stream_synthesis()` gets all script findings → streams Gemini response → parses `FINDING: label | desc | confidence` lines into `node_add` SSE events and `COMPLETE: summary` into `complete` event.

### Node Types
`NodeType = "goal" | "data_source" | "technique" | "question" | "finding"`

React Flow uses custom node components in `frontend/src/components/nodes/`. Node `type` field in React Flow maps to: `goalNode`, `dataSourceNode`, `techniqueNode`, `questionNode`, `findingNode`.

### SSE Event Types
- `log` → `{message: string}` — pipeline step text
- `node_add` → `{node: Node, edge: Edge}` — finding node to animate onto map
- `complete` → `{summary: string}` — triggers viz phase after 1.5s delay
- `script_complete` (internal, converted to `log` in `script_stream.py`)
- `modules_selected` (internal, converted to `log`)

### Key Files
- `backend/analysis/context.py` — `AnalysisContext` dataclass; shared state across all scripts
- `backend/analysis/modules.py` — `MODULE_REGISTRY` maps module names → script dotted paths; `MODULE_SELECTION_PROMPT`
- `backend/analysis/runner.py` — topological wave executor
- `backend/services/script_stream.py` — bridges pipeline queue → SSE generator → Gemini synthesis
- `backend/services/gemini_service.py` — all Gemini calls (map generation, module selection, streaming synthesis); model: `gemini-2.0-flash`
- `frontend/src/api/client.ts` — all fetch + SSE wrappers
- `frontend/src/types/graph.ts` — `DattackNode`, `DattackEdge`, `ContextRequest` types

## Adding a New Analysis Script

1. Create `backend/analysis/scripts/<module>/<name>.py`
2. Implement `DEPENDENCIES`, `is_applicable(ctx)`, `run(ctx)`
3. Register in `MODULE_REGISTRY` in `backend/analysis/modules.py`

## Environment

Backend needs `.env` in `backend/`:
```
GEMINI_API_KEY=...
```
