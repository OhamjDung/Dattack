import { useState } from 'react'
import ContextForm from './components/ContextForm'
import MapView from './components/MapView'
import AnalysisPanel from './components/AnalysisPanel'
import VizPanel from './components/VizPanel'
import { submitContext, approveMap } from './api/client'
import type { ContextRequest, DattackNode, DattackEdge } from './types/graph'

type Phase = 'context' | 'map' | 'analysis' | 'viz'

export default function App() {
  const [phase, setPhase] = useState<Phase>('context')
  const [loading, setLoading] = useState(false)
  const [graphState, setGraphState] = useState<{ nodes: DattackNode[]; edges: DattackEdge[] }>({ nodes: [], edges: [] })
  const [pendingSessionId, setPendingSessionId] = useState<string | undefined>()
  const [sessionId, setSessionId] = useState('')
  const [streamLog, setStreamLog] = useState<string[]>([])
  const [analysisNodes, setAnalysisNodes] = useState<DattackNode[]>([])
  const [analysisEdges, setAnalysisEdges] = useState<DattackEdge[]>([])

  async function handleContextSubmit(req: ContextRequest, file: File | null) {
    setLoading(true)
    try {
      const res = await submitContext(req, file)
      setGraphState({ nodes: res.nodes, edges: res.edges })
      setPendingSessionId(res.pending_session_id)
      setPhase('map')
    } finally {
      setLoading(false)
    }
  }

  async function handleApprove(nodes: DattackNode[], edges: DattackEdge[]) {
    const res = await approveMap(nodes, edges, pendingSessionId)
    setSessionId(res.session_id)
    setStreamLog([])
    setAnalysisNodes([])
    setAnalysisEdges([])
    setPhase('analysis')
  }

  function handleLog(msg: string) {
    setStreamLog((l) => [...l, msg])
  }

  function handleNodeAdd(node: DattackNode, edge: DattackEdge) {
    setAnalysisNodes((ns) => [...ns, node])
    setAnalysisEdges((es) => [...es, edge])
  }

  function handleComplete(summary: string) {
    setStreamLog((l) => [...l, `✓ ${summary}`])
    setTimeout(() => setPhase('viz'), 1500)
  }

  return (
    <>
      {phase === 'context' && (
        <ContextForm onSubmit={handleContextSubmit} loading={loading} />
      )}

      {(phase === 'map' || phase === 'analysis') && (
        <div className={phase === 'analysis' ? 'pb-56' : ''}>
          <MapView
            initialNodes={graphState.nodes}
            initialEdges={graphState.edges}
            onApprove={handleApprove}
            externalNodes={analysisNodes}
            externalEdges={analysisEdges}
          />
        </div>
      )}

      {phase === 'analysis' && (
        <AnalysisPanel
          sessionId={sessionId}
          log={streamLog}
          onLog={handleLog}
          onNodeAdd={handleNodeAdd}
          onComplete={handleComplete}
        />
      )}

      {phase === 'viz' && <VizPanel />}
    </>
  )
}
