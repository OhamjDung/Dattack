Plan: Phase 2 Curiosity Loop + Script Split                         
                                                                       
 Context                                                             
                                     
 Currently Phase 2 (Map) is a single blind Gemini call — no CSV data 
 informs the map, no loop, /research endpoint exists but is never    
 called. Phase 5 (Analysis) is the only place scripts run. The user
 wants:
 - Phase 2: AI is "curious" — runs exploratory scripts on the CSV,
 generates question/technique nodes, loops until nothing new to ask
 - Phase 5: AI executes the approved plan — runs analysis scripts,
 generates finding nodes
 - Scripts split into two purpose-built sets (~50 each)
 - Modular/composite scripts that chain sub-scripts (already supported
  via DEPENDENCIES — just write them)

 ---
 Current Status

 ┌────────────────┬─────────┬────────────────────────────────────┐
 │     Phase      │ Status  │                Gap                 │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 1 – Context    │ ✓       │ —                                  │
 │ Form           │ Working │                                    │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 2 – Map        │ ✗       │ Single blind Gemini call, no       │
 │ (curiosity)    │ Broken  │ scripts, no loop, /research never  │
 │                │         │ called                             │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 3 – Feedback   │ ✓       │ Gemini responds to node feedback   │
 │                │ Working │                                    │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 4 – Approve    │ ✓       │ —                                  │
 │                │ Working │                                    │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 5 – Analysis   │ ✓       │ 45 scripts + Gemini synthesis via  │
 │ Stream         │ Working │ SSE                                │
 ├────────────────┼─────────┼────────────────────────────────────┤
 │ 6 – Viz        │ ✗ Stub  │ Hardcoded mock charts              │
 └────────────────┴─────────┴────────────────────────────────────┘

 ---
 Architecture Changes

 Script Organization

 backend/analysis/
   curiosity_scripts/         ← NEW: Phase 2, question-generating
     foundation/              (same 3 scripts, reused)
     structure/               NEW: what is this data?
     signals/                 NEW: what's worth investigating?
     hypotheses/              NEW: what analyses make sense?
   analysis_scripts/          ← RENAME: Phase 5, finding-generating
     exploratory/             (existing 15 scripts)
     time_series/             (existing 11 scripts)
     ranking/                 (existing 5 scripts)
     business/                (existing 8 scripts)
     text/                    (existing 3 scripts)
     anomaly/                 (existing 3 scripts)

 Both sets use the same AnalysisContext dataclass and run(ctx) → dict
 contract. The difference is output intent: curiosity scripts output
 "question_candidates" and "technique_candidates" instead of
 "findings".

 Curiosity Script Output Shape

 {
   "script": "entity_type_guesser",
   "status": "ok",
   "question_candidates": [
     {"label": "...", "description": "...", "confidence": 0.8}
   ],
   "technique_candidates": [
     {"label": "...", "description": "...", "confidence": 0.7}
   ],
   "data": {}
 }

 MODULE_REGISTRY additions

 "curiosity": {
   "entity_type_guesser":
 "analysis.curiosity_scripts.structure.entity_type_guesser",
   "target_col_candidates":
 "analysis.curiosity_scripts.structure.target_col_candidates",
   "column_role_classifier":
 "analysis.curiosity_scripts.structure.column_role_classifier",
   "dataset_shape_classifier":
 "analysis.curiosity_scripts.structure.dataset_shape_classifier",
   "null_intent_detector":
 "analysis.curiosity_scripts.signals.null_intent_detector",
   "outlier_prevalence_screen":"analysis.curiosity_scripts.signals.out
 lier_prevalence_screen",
   "correlation_opportunity":
 "analysis.curiosity_scripts.signals.correlation_opportunity",
   "segment_variable_candidates":"analysis.curiosity_scripts.signals.s
 egment_variable_candidates",
   "temporal_coverage_analyzer":"analysis.curiosity_scripts.signals.te
 mporal_coverage_analyzer",
   "concentration_screen":
 "analysis.curiosity_scripts.signals.concentration_screen",
   "join_key_candidates":
 "analysis.curiosity_scripts.structure.join_key_candidates",
   "analysis_hypothesis_builder":"analysis.curiosity_scripts.hypothese
 s.analysis_hypothesis_builder",
   # ... expand to ~20-25 total
 }

 ---
 Backend Changes

 1. /context — script-grounded initial map

 File: backend/routers/context.py

 When CSV present:
 1. Parse CSV → DataFrame
 2. Run foundation curiosity scripts (schema_detector, field_profile,
 data_quality_report)
 3. Run curiosity module scripts in parallel
 4. Pass structured script outputs to
 gemini_service.generate_initial_map()

 When no CSV:
 - Same as now (text-only Gemini call)

 New gemini_service.generate_initial_map signature:
 generate_initial_map(goal, why, available_data, ideas,
 curiosity_outputs=None)
 If curiosity_outputs present, Gemini prompt includes script findings
 → generates grounded map.

 2. /research — curiosity loop iteration

 File: backend/routers/research.py

 Currently: single Gemini call, returns random nodes.
 New:
 1. Accept current map state (nodes with answered questions)
 2. Build AnalysisContext from session CSV + answered question
 metadata
 3. Run next wave of curiosity scripts (skipping already-asked
 questions)
 4. Gemini reads outputs + existing map → generates new
 question/technique nodes
 5. Returns {new_nodes: [], new_edges: []} when converged → frontend
 stops loop

 Convergence condition: Gemini returns empty OR all curiosity scripts
 are "skipped" or already covered by existing nodes.

 3. New curiosity_runner.py

 File: backend/analysis/curiosity_runner.py

 Same wave-executor pattern as runner.py but:
 - Loads curiosity scripts only
 - Collects question_candidates + technique_candidates from each
 script
 - Returns structured summary for Gemini to interpret
 - No Gemini synthesis step (Gemini is called in the router, not here)

 ---
 Frontend Changes

 Research Loop in App.tsx

 After /context returns initial map, start research loop:

 async function runResearchLoop(sessionId: string, nodes:
 DattackNode[]) {
   let currentNodes = nodes
   while (true) {
     const res = await runResearch(sessionId, currentNodes)
     if (res.new_nodes.length === 0) break
     currentNodes = mergeNodes(currentNodes, res.new_nodes)
     setGraphState(g => mergeGraph(g, res))
   }
   setResearching(false)
 }

 Add researching: boolean state → show "Researching…" overlay on map
 canvas.

 MapView — no changes needed

 Already handles external nodes merging via externalNodes prop.

 ---
 Curiosity Scripts to Build (~20 new scripts)

 structure/ (what is this data?)

 1. entity_type_guesser — entity / transaction / event / snapshot?
 2. target_col_candidates — which columns could be the dependent
 variable?
 3. column_role_classifier — ID / metric / category / flag / date /
 text per column
 4. dataset_shape_classifier — wide vs long, aggregated vs raw
 5. join_key_candidates — columns likely to join to other tables
 6. boolean_disguise_detector — 0/1 or Y/N columns masquerading as
 numeric/string
 7. id_column_validator — true unique ID vs near-ID vs overloaded key

 signals/ (what's worth investigating?)

 8. null_intent_detector — systematic vs random nulls → ask user
 intent
 9. outlier_prevalence_screen — quick z-score screen → flag for
 investigation
 10. correlation_opportunity — top correlated pairs → flag for
 analysis
 11. segment_variable_candidates — which categoricals divide data
 meaningfully?
 12. temporal_coverage_analyzer — date range, gaps, granularity
 13. concentration_screen — quick Gini → is this a Pareto situation?
 14. growth_signal_screen — if dates: is there obvious trend?
 15. anomaly_prevalence_screen — rough anomaly % → flag for anomaly
 analysis
 16. cardinality_screen — quick cardinality per categorical → ID vs
 usable feature

 hypotheses/ (what analyses are worth running?)

 17. analysis_hypothesis_builder — given schema + signals, what
 analyses make sense?
 18. missing_analysis_detector — what we DON'T know yet from the data
 19. composite_metric_opportunity — could multiple columns combine
 into an index?
 20. benchmark_opportunity_detector — is there a natural
 baseline/comparison group?

 Composite (chain multiple scripts, no new infra)

 - customer_value_profile → deps: [pareto_analysis, cohort_analysis,
 retention_curve]
 - market_concentration_report → deps: [concentration_analysis,
 pareto_analysis, segment_comparison]
 - time_series_full_suite → deps: [trend_analysis,
 seasonality_detection, changepoint_detection, forecast_baseline]

 ---
 Critical Files to Modify

 ┌────────────────────────────────────┬────────────────────────────┐
 │                File                │           Change           │
 ├────────────────────────────────────┼────────────────────────────┤
 │ backend/routers/context.py         │ Add curiosity pipeline     │
 │                                    │ when CSV present           │
 ├────────────────────────────────────┼────────────────────────────┤
 │ backend/routers/research.py        │ Wire up curiosity runner + │
 │                                    │  Gemini call               │
 ├────────────────────────────────────┼────────────────────────────┤
 │ backend/analysis/modules.py        │ Add "curiosity" to         │
 │                                    │ MODULE_REGISTRY            │
 ├────────────────────────────────────┼────────────────────────────┤
 │                                    │ Refactor to support        │
 │ backend/analysis/runner.py         │ curiosity mode (or create  │
 │                                    │ curiosity_runner.py)       │
 ├────────────────────────────────────┼────────────────────────────┤
 │                                    │ Update                     │
 │ backend/services/gemini_service.py │ generate_initial_map +     │
 │                                    │ generate_research_nodes to │
 │                                    │  accept script outputs     │
 ├────────────────────────────────────┼────────────────────────────┤
 │ frontend/src/App.tsx               │ Add research loop after    │
 │                                    │ context submit             │
 ├────────────────────────────────────┼────────────────────────────┤
 │ frontend/src/api/client.ts         │ Already has runResearch —  │
 │                                    │ just call it               │
 └────────────────────────────────────┴────────────────────────────┘

 ---
 New Files to Create

 - backend/analysis/curiosity_runner.py
 - backend/analysis/curiosity_scripts/__init__.py + subdirs
 - backend/analysis/curiosity_scripts/structure/*.py (7 scripts)
 - backend/analysis/curiosity_scripts/signals/*.py (9 scripts)
 - backend/analysis/curiosity_scripts/hypotheses/*.py (4 scripts)

 ---
 Verification

 1. Upload CSV → /context → map has nodes grounded in actual data (not
  hallucinated)
 2. Research loop fires automatically → new question/technique nodes
 appear on map
 3. Loop stops when no new questions → "Approve Map" becomes available
 4. Answer questions inline → click "Ask for deeper research" →
 /research fires again → more nodes
 5. Approve → SSE stream runs existing analysis pipeline → finding
 nodes animate onto map
 6. All 45 existing analysis scripts still run in phase 5 unmodified