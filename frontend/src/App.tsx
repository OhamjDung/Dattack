import { useState } from 'react'
import ContextForm from './components/ContextForm'
import MapView from './components/MapView'
import AnalysisPanel from './components/AnalysisPanel'
import VizPanel from './components/VizPanel'
import { submitContext, approveMap, runResearch } from './api/client'
import type { ContextRequest, DattackNode, DattackEdge } from './types/graph'

type Phase = 'context' | 'map' | 'analysis' | 'viz'

const MAX_RESEARCH_ROUNDS = 8
const MIN_RESEARCH_ROUNDS = 2

const PHASE_LABELS: Record<Phase, string> = {
  context: '01 Context',
  map: '02 Map',
  analysis: '03 Analysis',
  viz: '04 Results',
}

function mergeNodes(existing: DattackNode[], incoming: DattackNode[]): DattackNode[] {
  const ids = new Set(existing.map((n) => n.id))
  return [...existing, ...incoming.filter((n) => !ids.has(n.id))]
}

function mergeEdges(existing: DattackEdge[], incoming: DattackEdge[]): DattackEdge[] {
  const ids = new Set(existing.map((e) => e.id))
  return [...existing, ...incoming.filter((e) => !ids.has(e.id))]
}

function Nav({ phase, onPhaseClick }: { phase: Phase; onPhaseClick?: (p: Phase) => void }) {
  const phases: Phase[] = ['context', 'map', 'analysis', 'viz']
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      height: 64,
      background: 'rgba(232,226,217,0.96)',
      backdropFilter: 'blur(20px)',
      display: 'flex', alignItems: 'center', padding: '0 36px', gap: 24,
      boxShadow: '0 4px 0 0 rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.06)',
    }}>
      <div style={{
        fontFamily: 'var(--font-display)', fontSize: 17, fontWeight: 900,
        letterSpacing: 3, color: 'var(--black)',
        display: 'flex', alignItems: 'center', gap: 10, marginRight: 'auto',
      }}>
        <div style={{ width: 10, height: 10, background: 'var(--orange)', borderRadius: '50%', boxShadow: '0 3px 0 rgba(180,40,0,0.5)' }} />
        DATTACK
      </div>
      <div style={{ display: 'flex', gap: 28 }}>
        {phases.map((p) => (
          <a key={p}
            onClick={() => onPhaseClick?.(p)}
            style={{
              fontSize: 12, fontWeight: 700, letterSpacing: '1.5px',
              textTransform: 'uppercase',
              color: phase === p ? 'var(--orange)' : '#4a4540',
              textDecoration: 'none', cursor: 'pointer', transition: 'color .15s',
            }}>
            {PHASE_LABELS[p]}
          </a>
        ))}
      </div>
      <span style={{
        fontSize: 11, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase',
        background: 'var(--orange)', color: '#fff',
        padding: '6px 14px', borderRadius: 999,
        boxShadow: '0 4px 0 rgba(180,40,0,0.6), 0 6px 12px rgba(255,69,0,0.2)',
      }}>
        {PHASE_LABELS[phase]}
      </span>
    </nav>
  )
}

export default function App() {
  const [phase, setPhase] = useState<Phase>('context')
  const [loading, setLoading] = useState(false)
  const [graphNodes, setGraphNodes] = useState<DattackNode[]>([])
  const [graphEdges, setGraphEdges] = useState<DattackEdge[]>([])
  const [researchNodes, setResearchNodes] = useState<DattackNode[]>([])
  const [researchEdges, setResearchEdges] = useState<DattackEdge[]>([])
  const [researching, setResearching] = useState(false)
  const [researchWave, setResearchWave] = useState(0)
  const [researchLabel, setResearchLabel] = useState('')
  const [pendingSessionId, setPendingSessionId] = useState<string | undefined>()
  const [sessionId, setSessionId] = useState('')
  const [streamLog, setStreamLog] = useState<string[]>([])
  const [analysisNodes, setAnalysisNodes] = useState<DattackNode[]>([])
  const [analysisEdges, setAnalysisEdges] = useState<DattackEdge[]>([])
  const [isComplete, setIsComplete] = useState(false)
  const [activeScript, setActiveScript] = useState('')

  async function runResearchLoop(pid: string, initialNodes: DattackNode[], initialEdges: DattackEdge[]) {
    setResearching(true)
    let nodes = initialNodes
    let edges = initialEdges

    for (let i = 0; i < MAX_RESEARCH_ROUNDS; i++) {
      setResearchWave(i + 1)
      setResearchLabel(`research wave ${i + 1}`)
      try {
        const res = await runResearch(pid, [...nodes, ...researchNodes])
        if (!res.new_nodes.length) break
        nodes = mergeNodes(nodes, res.new_nodes)
        edges = mergeEdges(edges, res.new_edges)
        setResearchNodes(ns => mergeNodes(ns, res.new_nodes))
        setResearchEdges(es => mergeEdges(es, res.new_edges))
        if (!res.has_more && i >= MIN_RESEARCH_ROUNDS - 1) break
      } catch {
        break
      }
    }

    setResearching(false)
    setResearchLabel('')
  }

  async function handleContextSubmit(req: ContextRequest, file: File | null) {
    setLoading(true)
    try {
      const res = await submitContext(req, file)
      const pid = res.pending_session_id
      setPendingSessionId(pid)
      setGraphNodes(res.nodes)
      setGraphEdges(res.edges)
      setResearchNodes([])
      setResearchEdges([])
      setResearchWave(0)
      setPhase('map')
      if (pid) runResearchLoop(pid, res.nodes, res.edges)
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(nodes: DattackNode[], edges: DattackEdge[]) {
    const allNodes = mergeNodes(nodes, researchNodes)
    const allEdges = mergeEdges(edges, researchEdges)
    const res = await approveMap(allNodes, allEdges, pendingSessionId)
    setSessionId(res.session_id)
    setStreamLog([])
    setAnalysisNodes([])
    setAnalysisEdges([])
    setIsComplete(false)
    setPhase('analysis')
  }

  function handleLog(msg: string) { setStreamLog((l) => [...l, msg]) }
  function handleNodeAdd(node: DattackNode, edge: DattackEdge) {
    setAnalysisNodes((ns) => [...ns, node])
    setAnalysisEdges((es) => [...es, edge])
  }
  function handleComplete(summary: string) {
    setStreamLog((l) => [...l, `✓ ${summary}`])
    setIsComplete(true)
    setTimeout(() => setPhase('viz'), 1800)
  }

  const allMapNodes = mergeNodes(graphNodes, researchNodes)
  const allMapEdges = mergeEdges(graphEdges, researchEdges)

  return (
    <>
      <Nav phase={phase} />
      {phase === 'context' && (
        <ContextForm onSubmit={handleContextSubmit} loading={loading} />
      )}
      {phase === 'map' && (
        <MapView
          nodes={graphNodes}
          edges={graphEdges}
          externalNodes={researchNodes}
          externalEdges={researchEdges}
          onApprove={handleApprove}
          researching={researching}
          researchWave={researchWave}
          researchLabel={researchLabel}

        />
      )}
      {phase === 'analysis' && (
        <>
          <MapView
            nodes={allMapNodes}
            edges={allMapEdges}
            externalNodes={analysisNodes}
            externalEdges={analysisEdges}
            onApprove={() => {}}
            isAnalysis
            activeScript={activeScript}
          />
          <AnalysisPanel
            sessionId={sessionId}
            log={streamLog}
            onLog={handleLog}
            onNodeAdd={handleNodeAdd}
            onComplete={handleComplete}
            onScriptRunning={setActiveScript}
            isComplete={isComplete}
          />
        </>
      )}
      {phase === 'viz' && (
        <VizPanel
          nodes={mergeNodes(allMapNodes, analysisNodes)}
          edges={mergeEdges(allMapEdges, analysisEdges)}
          streamLog={streamLog}
        />
      )}
    </>
  )
}
