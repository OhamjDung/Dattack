     Dattack — Revised Architecture & Scaffold Plan

     Context

     Building a Human-in-the-Loop AI Data Consultant. The repo is empty. The core UX is a React Flow node map — not a step wizard. The user provides context, the AI builds a
     living map of how data sources connect to their goal, inline question nodes prompt the user for clarification, and after approval the AI streams its analysis live before
     producing interactive visualizations.

     Stack:
     - Frontend: React + Vite + Tailwind CSS (light theme) + React Flow
     - Backend: Python + FastAPI with SSE (Server-Sent Events) for streaming
     - LLM: Claude API (placeholder now, wired in later)
     - App name: Dattack

     ---
     User Flow

     1. Context Form
        └─ Why this analysis / Goal / Available datasets / Ideas

     2. React Flow Map (appears immediately, evolves live)
        ├─ Goal node (center)
        ├─ Data source nodes (uploaded files + AI-discovered sources)
        ├─ Technique nodes (connecting data → goal)
        ├─ Question nodes (AI asks clarifying questions inline)
        └─ Finding nodes (populated after analysis)

     3. Map Fine-Tuning
        ├─ Click any node → feedback/deeper-research panel
        └─ AI responds by adding/modifying nodes

     4. User approves the map

     5. AI Analysis (live streaming log)
        ├─ SSE stream shows AI reasoning steps in real time
        ├─ Finding nodes animate onto the map as discoveries happen
        └─ Patterns, correlations, anomalies, trends

     6. Interactive Visualizations
        └─ Charts rendered in-app from analysis findings

     ---
     Directory Structure

     Dattack/
     ├── backend/
     │   ├── main.py                    # FastAPI app, CORS, SSE support
     │   ├── requirements.txt
     │   ├── routers/
     │   │   ├── context.py             # POST /context — receive user context, return initial map
     │   │   ├── research.py            # POST /research — AI discovers data sources, returns nodes
     │   │   ├── feedback.py            # POST /feedback — node-level feedback, returns updated nodes
     │   │   ├── approve.py             # POST /approve — lock map, start analysis
     │   │   └── stream.py              # GET /stream — SSE endpoint for live analysis log
     │   ├── services/
     │   │   └── placeholder.py         # Stub functions returning mock nodes/findings
     │   └── schemas/
     │       └── models.py              # Pydantic models for nodes, edges, stream events
     ├── frontend/
     │   ├── package.json
     │   ├── vite.config.ts
     │   ├── tailwind.config.ts
     │   ├── index.html
     │   └── src/
     │       ├── main.tsx
     │       ├── App.tsx                # Root: phase state (context → map → analysis → viz)
     │       ├── api/
     │       │   └── client.ts          # Typed fetch + SSE wrappers
     │       ├── types/
     │       │   └── graph.ts           # Node/Edge type definitions
     │       └── components/
     │           ├── ContextForm.tsx    # Initial context input (phase 1)
     │           ├── MapView.tsx        # React Flow canvas wrapper (phase 2-3)
     │           ├── AnalysisPanel.tsx  # Live streaming log sidebar (phase 5)
     │           ├── VizPanel.tsx       # Interactive charts output (phase 6)
     │           └── nodes/
     │               ├── GoalNode.tsx        # Central goal node
     │               ├── DataSourceNode.tsx  # Dataset node (uploaded or discovered)
     │               ├── TechniqueNode.tsx   # Analysis method node
     │               ├── QuestionNode.tsx    # Inline AI clarifying question
     │               └── FindingNode.tsx     # Post-analysis insight node
     └── README.md

     ---
     API Contract (placeholder responses)

     ┌───────────┬───────────┬───────────────────────────────────────────────────────────────────────────────────┐
     │ Endpoint  │  Method   │                                      Returns                                      │
     ├───────────┼───────────┼───────────────────────────────────────────────────────────────────────────────────┤
     │ /context  │ POST      │ {nodes: Node[], edges: Edge[]} — initial map with goal + uploaded data nodes      │
     ├───────────┼───────────┼───────────────────────────────────────────────────────────────────────────────────┤
     │ /research │ POST      │ {new_nodes: Node[], new_edges: Edge[]} — discovered data sources + question nodes │
     ├───────────┼───────────┼───────────────────────────────────────────────────────────────────────────────────┤
     │ /feedback │ POST      │ {updated_nodes: Node[], new_edges: Edge[]} — map changes from node feedback       │
     ├───────────┼───────────┼───────────────────────────────────────────────────────────────────────────────────┤
     │ /approve  │ POST      │ {session_id: string, status: "analysis_started"}                                  │
     ├───────────┼───────────┼───────────────────────────────────────────────────────────────────────────────────┤
     │ /stream   │ GET (SSE) │ event: log | node_add | complete — streaming analysis events                      │
     └───────────┴───────────┴───────────────────────────────────────────────────────────────────────────────────┘

     Node schema (shared)

     type NodeType = "goal" | "data_source" | "technique" | "question" | "finding"
     type NodeData = {
       label: string
       description: string
       type: NodeType
       status?: "pending" | "active" | "answered" | "complete"
       metadata?: Record<string, unknown>  // source URL, row count, correlation score, etc.
     }

     SSE stream event types

     event: log      → { message: string }          // reasoning step text
     event: node_add → { node: Node, edge: Edge }   // new finding node to add to map
     event: complete → { summary: string }          // analysis done

     ---
     Implementation Steps

     1. Backend scaffold

     - main.py: FastAPI with CORS for localhost:5173, SSE via sse-starlette
     - schemas/models.py: Node, Edge, StreamEvent Pydantic models
     - All 5 routers return hardcoded mock data matching schema
     - /stream returns a mock SSE sequence (3 log events → 2 node_add events → complete)
     - requirements.txt: fastapi, uvicorn, sse-starlette, python-multipart, anthropic

     2. Frontend scaffold

     - Init: npm create vite@latest frontend -- --template react-ts
     - Install: tailwindcss, reactflow, lucide-react, axios
     - Light theme: white bg, slate-100 canvas, indigo (#4F46E5) accent, slate-700 text

     3. App.tsx phase state

     - phase: "context" | "map" | "analysis" | "viz"
     - graphState: {nodes, edges} — single source of truth for the map
     - streamLog: string[] — accumulated analysis log lines

     4. ContextForm.tsx

     - Four labeled text areas: Goal, Why, Available Data (file upload + text description), Ideas/Techniques
     - "Start Research" button → calls /context → transitions to map phase

     5. MapView.tsx + React Flow

     - Full-screen React Flow canvas with custom node types registered
     - Floating "Approve Map" button (bottom-right, disabled until no open question nodes)
     - Node click → NodeDetailPanel slides in from right with feedback textarea + "Ask for deeper research" button
     - Calls /feedback on submit, merges returned nodes into graph state

     6. Custom node components

     - GoalNode: Large indigo card, centered, star icon
     - DataSourceNode: Blue card, database icon, shows row count + source badge
     - TechniqueNode: Purple card, shows method name + which datasets it connects
     - QuestionNode: Amber card, question-mark icon, inline answer input field
     - FindingNode: Green card (appears during analysis), trend icon, finding text

     7. AnalysisPanel.tsx

     - Side drawer that opens on map approval
     - Consumes SSE from /stream via EventSource
     - Appends log messages in real time with a pulsing cursor
     - On node_add events: calls setNodes to add finding nodes to the live map
     - On complete: transitions to viz phase

     8. VizPanel.tsx

     - Placeholder chart area (use mock data)
     - Will render interactive charts (Recharts or similar) in a later phase

     ---
     Verification

     1. cd backend && uvicorn main:app --reload — all endpoints return 200 with correct mock shapes
     2. cd frontend && npm run dev — app loads at localhost:5173
     3. Fill context form → map renders with goal node + 2 mock data nodes + 1 question node
     4. Click question node → answer it → question node turns green, "Approve" button enables
     5. Click "Approve" → analysis panel opens, log streams 3 lines, 2 finding nodes animate onto map
     6. Viz panel appears with placeholder charts





       during (2)                                                           
                                                                       
  do we have an AI loop where the AI investigates until there is       
  nothing "left" to investigate? We're using all of the scripts we     
  built here right?                                                    
                                                                       
  we can have Exploratory Scripts (50 Scripts) for (2) and Analysis    
  Scripts (50 scripts) for (5)                                         
                                                                       
  basically, for (2), the goal is to have questions that we need to    
  answer, basically explore to get a plan                              
                                                                       
       4. User approves the map                                        
                                                                       
       5. AI Analysis (live streaming log)                             
          ├─ SSE stream shows AI reasoning steps in real time          
          ├─ Finding nodes animate onto the map as discoveries happen  
          └─ Patterns, correlations, anomalies, trends                 
                                                                       
       6. Interactive Visualizations                                   
          └─ Charts rendered in-app from analysis findings             
                                                                       
                                                                       
  so this flow is working?                                             
                                                                       
  during (2)                                                           
                                                                       
  do we have an AI loop where the AI investigates until there is       
  nothing "left" to investigate? We're using all of the scripts we     
  built here right?                                                    
                                                                       
  we can have Exploratory Scripts (50 Scripts) for (2) and Analysis    
  Scripts (50 scripts) for (5)                                         
                                                                       
  basically, for (2), the goal is to have questions that we need to    
  answer, basically explore to get a plan                              
                                                                       
  and we have the user (3) to fine tune that plan and add THEIR        
  questions                                                            
                                                                       
  so basically, have the AI be curious in (2)                          
                                                                       
  and then (5) is when it executes that plan                           
                                                                       
  also remember that you can make "modular" scripts too, or have       
  scripts modules that can be chained together to make bigger scripts  

● What's actually working right now:               
  - Phase 1 ✓ (context form → /context → initial map)                
  - Phase 3 ✓ (node click → feedback → map updates)                    
  - Phase 4 ✓ (approve → session stored)
  - Phase 5 ✓ (SSE pipeline + Gemini synthesis + finding nodes animate)
  - Phase 2 ✗ no research loop — single Gemini call builds map,      
  /research exists but nothing calls it                                
  - Phase 6 ✗ placeholder only                                       
                                               
  ---                                                                
  Your vision is solid. Here's what it implies architecturally:

  Phase 2 — Exploratory Scripts (curiosity loop)

  Goal isn't findings — it's generating questions and a plan. Scripts
  should output things like:
  - "target column is ambiguous — 3 candidates"
  - "date column detected but granularity unclear (day vs week?)"
  - "high cardinality in customer_id — could be entity or transaction
  data"

  Each output → Gemini reads it → adds question or technique nodes to
  map → loop repeats until no new questions surface. User answers
  inline → /research called again with updated answers → loop.

  Phase 5 — Analysis Scripts (execution)

  Current pipeline is already this. Runs the approved plan, produces
  findings, streams them as nodes.

  ---
  Proposed split:

  analysis/
    exploratory_scripts/   ← phase 2: fast, question-generating
      foundation/          ← schema, profile, quality (shared with
  phase 5)
      structure/           ← ambiguity detectors, entity-type guesser
      relationships/       ← what connects to what, what's missing
      hypotheses/          ← generates candidate analyses to run

    analysis_scripts/      ← phase 5: current scripts, produces
  findings
      exploratory/
      time_series/
      ranking/
      business/
      text/
      anomaly/

  Modular/chainable scripts — already works via DEPENDENCIES. Could
  formalize "composite" scripts that just chain sub-scripts and
  aggregate their outputs, no new infra needed.

  ---
  The key design question before building: Does the phase 2 loop run
  scripts on the CSV directly, or does Gemini drive the curiosity
  purely from the foundation summary? If CSV is available, scripts can
  be concrete ("27% nulls in revenue — what should we do?"). If no CSV
  yet, it's pure Gemini speculation.

  What's the expected state at phase 2 — CSV always uploaded, or
  optional?