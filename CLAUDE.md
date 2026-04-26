# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Dattack — Human-in-the-Loop AI Data Consultant. User provides a CSV + goal. The system builds a live React Flow node map, runs a deterministic script pipeline against the data, then an LLM synthesises findings via SSE streaming and animates finding nodes onto the map.

**LLM backend:** GitHub Models via OpenAI-compatible API at `https://models.github.ai/inference`. Default model: `openai/gpt-4o-mini` (Low tier: 15 RPM / 150 RPD). All LLM calls go through `backend/services/gemini_service.py` (name kept for compatibility).

**Model rate limits (GitHub Models free tier):**
- `openai/gpt-4o-mini` — Low: 15 RPM, 150 RPD ← current default
- `deepseek/DeepSeek-R1-0528` — DeepSeek tier: 1 RPM, 8 RPD (avoid — too restrictive)
- To switch models: edit `_MODEL` at top of `backend/services/gemini_service.py`

**Dead files** (leftover from initial Claude API prototype, not used): `backend/services/claude_service.py`, `backend/services/claude_stream.py`.

---

## User Flow

```
1. User lands on context page
   └─ Fills in: goal, why it matters, available data description, ideas
   └─ Optionally uploads a CSV file

2. "Build Map" button → POST /context
   └─ If CSV: curiosity pipeline runs (deterministic, no LLM) → produces question/technique candidates
   └─ LLM brainstorms 10 investigative angles (non-obvious paths)
   └─ LLM generates initial node map (goal + data_source + technique + question nodes)
   └─ Frontend enters MAP phase, shows node graph

3. Research loop (min 2, max 8 rounds, dynamic)
   └─ POST /research → LLM adds more technique/question nodes grounded in remaining candidates
   └─ Backend returns has_more=true/false to decide whether to continue
   └─ Nodes animate onto map

4. User reviews map
   └─ Can click any node → give feedback → POST /feedback → LLM returns insight nodes
   └─ Can drag nodes to rearrange, zoom in/out with scroll or +/- buttons
   └─ "Approve Map" always available (no gate on question nodes)

5. "Approve Map" → POST /approve
   └─ Pending session promoted to final session
   └─ Frontend enters ANALYSIS phase

6. GET /stream?session_id=... (SSE)
   └─ Foundation scripts run (schema, profile, quality)
   └─ LLM selects up to 4 analysis modules
   └─ Module scripts run in topological waves
   └─ LLM streams synthesis: emits FINDING lines → animated finding nodes
   └─ COMPLETE line → frontend enters VIZ phase

7. VIZ phase
   └─ Full node map shown with all findings
   └─ Stream log displayed
```

---

## Data Flow

```
CSV upload
  │
  ▼
POST /context
  ├─ curiosity_runner.py → runs curiosity_scripts/** deterministically
  │     └─ outputs: question_candidates[], technique_candidates[], data_summary
  │
  └─ gemini_service.generate_initial_map(goal, why, data, ideas, curiosity_outputs)
        ├─ _brainstorm() → LLM generates 10 non-obvious investigative angles
        └─ LLM → JSON {nodes, edges} (grounded in brainstorm + curiosity outputs)
        └─ stored in session_store as pending_{id}

POST /research (min 2, max 8 rounds)
  └─ gemini_service.generate_research_nodes(nodes, goal, curiosity_outputs, iteration)
        └─ LLM → JSON {nodes, edges} (only new nodes not already in map)
        └─ returns (nodes, edges, has_more: bool)
        └─ has_more computed from remaining curiosity candidates

POST /feedback
  └─ gemini_service.process_feedback(node, all_nodes, feedback, deeper)
        └─ LLM → JSON {nodes, edges} using node_type "insight" for feedback-driven nodes

POST /approve
  └─ session_store: pending_{id} → {session_id}
        stores: nodes, edges, goal, csv_bytes

GET /stream
  └─ script_stream.py orchestrates:
        ├─ runner.py Phase 1: schema_detector → field_profile → data_quality_report
        │     populates AnalysisContext (ctx.schema, ctx.profile, ctx.quality)
        ├─ gemini_service.select_modules(foundation_summary, goal)
        │     └─ LLM picks ≤4 from: exploratory, time_series, ranking, business, text, anomaly
        ├─ runner.py Phase 2: selected module scripts run in topological waves (ThreadPoolExecutor)
        │     each script: is_applicable(ctx) → run(ctx) → {status, findings[], data}
        └─ gemini_service.stream_synthesis(ctx)
              └─ LLM streams → parses lines:
                    FINDING: label | desc | confidence  →  node_add SSE event
                    COMPLETE: summary                   →  complete SSE event
                    anything else                       →  log SSE event
```

---

## Dev Commands

**Quick start:**
```bash
run.bat    # Windows — installs deps, starts backend + frontend
```

Requires `backend/.env` with GitHub token:
```
GITHUB_TOKEN=your_github_pat_with_models_read_scope
```

**Mock mode** (no LLM calls, instant hardcoded nodes — for frontend dev):
```
# in backend/.env
MOCK_MODE=true
```
Remove or set `MOCK_MODE=` to go back to real LLM.

**Manual — Backend** (from `backend/`):
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
Runs at `http://localhost:8000`.

**Manual — Frontend** (from `frontend/`):
```bash
npm install
npm run dev      # dev server at localhost:5173
npm run build    # tsc -b && vite build
npm run lint     # eslint
```

---

## Architecture

### Phase State Machine (frontend)
`App.tsx` owns phase: `context → map → analysis → viz`. Single source of truth for `graphState` (nodes + edges), `streamLog`, and `sessionId`.

### API Flow
1. `POST /context` (multipart/form-data with optional CSV) → curiosity pipeline if CSV → brainstorm → initial node map + `pending_session_id`
2. `POST /research` → add technique/question nodes (min 2, max 8 rounds, `has_more` controls continuation)
3. `POST /feedback` → update nodes based on user feedback; returns `insight` type nodes
4. `POST /approve` → promotes pending session, returns `session_id`
5. `GET /stream?session_id=...` → SSE stream of pipeline + synthesis events

Session state in `services/session_store.py` (in-memory dict):
- `pending_{id}` — CSV bytes + curiosity outputs while map is being built
- `{session_id}` — final session after approve; includes nodes, edges, goal, csv_bytes

### Curiosity Pipeline (`backend/analysis/curiosity_runner.py`)
Runs deterministically (no LLM) on CSV upload before map is shown. Outputs `question_candidates` and `technique_candidates` (with confidence scores) so the LLM builds a data-grounded map.

Script categories in `analysis/curiosity_scripts/`:
- `structure/` — entity type, target column, column roles, dataset shape, join keys
- `signals/` — nulls, outliers, correlations, segments, temporal coverage, concentration, growth, anomalies
- `hypotheses/` — candidate analyses, missing analysis detection, composite metrics, benchmarks

### Analysis Pipeline (`backend/analysis/`)

**Phase 1 — Foundation (always runs):**
- `schema_detector` → populates `AnalysisContext.schema`, column type lists
- `field_profile` → populates `ctx.profile`
- `data_quality_report` → populates `ctx.quality`

**Phase 2 — Module selection + execution:**
- LLM (`select_modules`) picks up to 4 modules from: `exploratory`, `time_series`, `ranking`, `business`, `text`, `anomaly`
- Scripts run in topological waves (parallel within each wave) via `ThreadPoolExecutor`
- Each script implements: `DEPENDENCIES: list[str]`, `is_applicable(ctx) -> bool`, `run(ctx) -> dict`
- `run()` returns `{"status": "ok"|"skipped"|"error", "findings": [...], "data": {...}}`

**Phase 3 — Synthesis:**
`gemini_service.stream_synthesis()` feeds all script findings to LLM → streams response → parses `FINDING: label | desc | confidence` lines into `node_add` SSE events and `COMPLETE: summary` into `complete` event.

### LLM Service (`backend/services/gemini_service.py`)
Uses `openai` SDK pointed at GitHub Models (`https://models.github.ai/inference`, api_key from `GITHUB_TOKEN` env).
- All responses run through `_strip_think()` — removes `<think>...</think>` blocks from DeepSeek R1
- `_brainstorm()` — pre-step before map generation; LLM produces 10 non-obvious investigative angles
- `_MOCK_MODE` — set `MOCK_MODE=true` in env to skip all LLM calls and return hardcoded nodes
- Sync calls (`_call`): `generate_initial_map`, `generate_research_nodes`, `process_feedback`
- Async calls (`_acall` / streaming): `select_modules`, `stream_synthesis`
- Change model: set `_MODEL` at top of file (default: `"deepseek/DeepSeek-R1-0528"`)
- Node positioning uses `type_offset` so research round nodes never overlap existing nodes

### Node Types
`NodeType = "goal" | "data_source" | "technique" | "question" | "finding" | "insight"`

- `insight` — created only by user feedback (`process_feedback`), distinct teal color, never by map generation
- `question` — read-only display nodes (no interactive input/answer)
- All types can chain to any other type via edges (no forced star topology to goal-1)

Layout columns (x positions): data_source=80, technique=380, goal=580, question=880, finding/insight=1280

### Map View (`frontend/src/components/MapView.tsx`)
Custom HTML canvas (not React Flow canvas — only uses RF `Handle` components).
- Pan: drag empty canvas space
- Node drag: drag individual node cards
- Zoom: mouse wheel or +/−/RESET buttons in toolbar (0.25× – 3.0×)
- Feedback popup: click any node → textarea → "Update" or "Deep Research"
- Approve Map always enabled (no gate on question node status)

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
- `backend/services/script_stream.py` — bridges pipeline queue → SSE generator → LLM synthesis
- `backend/services/gemini_service.py` — all LLM calls (brainstorm, map generation, module selection, streaming synthesis)
- `frontend/src/api/client.ts` — all fetch + SSE wrappers
- `frontend/src/types/graph.ts` — `DattackNode`, `DattackEdge`, `ContextRequest` types
- `frontend/src/components/MapView.tsx` — canvas, pan/zoom, node render, feedback popup

---

## Adding Scripts

**Analysis script** (produces findings after user approves map):
1. Create `backend/analysis/scripts/<module>/<name>.py`
2. Implement `DEPENDENCIES`, `is_applicable(ctx)`, `run(ctx) → {"status", "findings", "data"}`
3. Register in `MODULE_REGISTRY` in `backend/analysis/modules.py`

**Curiosity script** (runs on CSV upload, generates map questions/techniques):
1. Create `backend/analysis/curiosity_scripts/<category>/<name>.py`
2. Implement `DEPENDENCIES`, `is_applicable(ctx)`, `run(ctx) → {"status", "question_candidates", "technique_candidates", "data"}`
3. Register in `CURIOSITY_REGISTRY` in `backend/analysis/curiosity_runner.py`

Each candidate item: `{"label": str, "description": str, "confidence": float 0–1}`

---

## Environment

`backend/.env`:
```
GITHUB_TOKEN=your_github_pat        # required — models:read scope
MOCK_MODE=true                      # optional — skip LLM, return hardcoded nodes
```

To switch models: edit `_MODEL` in `backend/services/gemini_service.py`.
