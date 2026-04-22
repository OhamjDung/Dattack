import { useState, useEffect, useRef, useCallback } from 'react'
import type { DattackNode, DattackEdge } from '../types/graph'
import { submitFeedback } from '../api/client'

const NODE_COLORS: Record<string, { bg: string; fg: string; label: string }> = {
  goal:        { bg: '#FF4500', fg: '#fff', label: 'Goal' },
  data_source: { bg: '#1A56DB', fg: '#fff', label: 'Data' },
  technique:   { bg: '#6B21A8', fg: '#fff', label: 'Technique' },
  question:    { bg: '#B45309', fg: '#fff', label: 'Question' },
  finding:     { bg: '#065F46', fg: '#fff', label: 'Finding' },
}

interface Props {
  nodes: DattackNode[]
  edges: DattackEdge[]
  externalNodes?: DattackNode[]
  externalEdges?: DattackEdge[]
  onApprove: (nodes: DattackNode[], edges: DattackEdge[]) => void
  isAnalysis?: boolean
  researching?: boolean
  researchWave?: number
  researchLabel?: string
  totalWaves?: number
}

export default function MapView({
  nodes: initNodes,
  edges: initEdges,
  externalNodes = [],
  externalEdges = [],
  onApprove,
  isAnalysis = false,
  researching = false,
  researchWave = 0,
  researchLabel = '',
  totalWaves = 3,
}: Props) {
  const [nodes, setNodes] = useState<DattackNode[]>(initNodes)
  const [edges, setEdges] = useState<DattackEdge[]>(initEdges)
  const [selected, setSelected] = useState<DattackNode | null>(null)
  const [popupPos, setPopupPos] = useState({ x: 0, y: 0 })
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [dragging, setDragging] = useState<{ id: string; startX: number; startY: number } | null>(null)
  const [panning, setPanning] = useState<{ startX: number; startY: number } | null>(null)
  const [panOffset, setPanOffset] = useState({ x: 60, y: 40 })
  const containerRef = useRef<HTMLDivElement>(null)
  const didMove = useRef(false)

  // Sync initial nodes/edges when parent updates them
  useEffect(() => { setNodes(initNodes) }, [initNodes])
  useEffect(() => { setEdges(initEdges) }, [initEdges])

  // Merge external nodes
  useEffect(() => {
    if (!externalNodes.length) return
    setNodes((ns) => {
      const ids = new Set(ns.map((n) => n.id))
      const incoming = externalNodes.filter((n) => !ids.has(n.id))
      return incoming.length ? [...ns, ...incoming] : ns
    })
  }, [externalNodes])

  useEffect(() => {
    if (!externalEdges.length) return
    setEdges((es) => {
      const ids = new Set(es.map((e) => e.id))
      const incoming = externalEdges.filter((e) => !ids.has(e.id))
      return incoming.length ? [...es, ...incoming] : es
    })
  }, [externalEdges])

  const hasOpenQ = nodes.some((n) => n.data.type === 'question' && n.data.status !== 'answered')

  function handleNodeMouseDown(e: React.MouseEvent, node: DattackNode) {
    e.stopPropagation()
    didMove.current = false
    setDragging({ id: node.id, startX: e.clientX - node.position.x, startY: e.clientY - node.position.y })
  }

  function handleCanvasMouseDown(e: React.MouseEvent) {
    const tgt = e.target as HTMLElement
    if (tgt !== containerRef.current && !tgt.closest('svg')) return
    didMove.current = false
    setPanning({ startX: e.clientX - panOffset.x, startY: e.clientY - panOffset.y })
  }

  const onMove = useCallback((e: MouseEvent) => {
    if (dragging) {
      didMove.current = true
      setNodes((ns) => ns.map((n) => n.id === dragging.id
        ? { ...n, position: { x: e.clientX - dragging.startX, y: e.clientY - dragging.startY } }
        : n))
    } else if (panning) {
      didMove.current = true
      setPanOffset({ x: e.clientX - panning.startX, y: e.clientY - panning.startY })
    }
  }, [dragging, panning])

  const onUp = useCallback(() => {
    setDragging(null)
    setPanning(null)
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp) }
  }, [onMove, onUp])

  function handleNodeClick(e: React.MouseEvent, node: DattackNode) {
    if (didMove.current) return
    e.stopPropagation()
    const rect = containerRef.current?.getBoundingClientRect()
    setPopupPos({ x: e.clientX - (rect?.left ?? 0) + 10, y: e.clientY - (rect?.top ?? 0) + 10 })
    setSelected(node)
    setFeedback('')
  }

  async function handleFeedbackSubmit(deeper: boolean) {
    if (!selected || !feedback.trim()) return
    setSubmitting(true)
    try {
      const res = await submitFeedback(selected.id, feedback, deeper, nodes as any)
      setNodes((ns) => {
        const updatedMap = new Map(res.updated_nodes.map((n) => [n.id, n]))
        const merged = ns.map((n) => updatedMap.has(n.id) ? { ...n, ...updatedMap.get(n.id)! } : n)
        const brandNew = res.updated_nodes.filter((n) => !ns.find((e) => e.id === n.id))
        return [...merged, ...brandNew] as DattackNode[]
      })
      setEdges((es) => [...es, ...res.new_edges as DattackEdge[]])
      setSelected(null)
    } catch {
      // Optimistic update on error
      setNodes((ns) => ns.map((n) =>
        n.id === selected.id ? { ...n, data: { ...n.data, status: 'answered', description: feedback } } : n
      ))
      setSelected(null)
    } finally {
      setSubmitting(false)
    }
  }

  function getCenter(node: DattackNode) {
    return { x: node.position.x + panOffset.x + 88, y: node.position.y + panOffset.y + 38 }
  }

  const cursorStyle = panning ? 'grabbing' : dragging ? 'grabbing' : 'grab'
  const canvasWidth = isAnalysis ? 'calc(100% - 320px)' : '100%'
  const canvasHeight = isAnalysis ? 'calc(100vh - 64px)' : 'calc(100vh - 64px - 46px)'

  return (
    <div style={{ paddingTop: 64 }}>
      {/* Toolbar */}
      {!isAnalysis && (
        <div style={{
          padding: '10px 32px',
          borderBottom: '1px solid var(--line)',
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
          height: 46,
        }}>
          {researching ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="pulse-dot" />
              <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--orange)' }}>
                Researching…
              </span>
              <span style={{ fontSize: 11, color: 'var(--gray)', fontWeight: 500 }}>
                Wave {researchWave}/{totalWaves}
              </span>
            </div>
          ) : (
            <button
              className="btn-primary"
              onClick={() => onApprove(nodes, edges)}
              disabled={hasOpenQ}
              style={{ padding: '10px 24px', fontSize: 12 }}
            >
              Approve Map →
            </button>
          )}
        </div>
      )}

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{ position: 'relative', width: canvasWidth, height: canvasHeight, overflow: 'hidden', cursor: cursorStyle }}
        onClick={() => { if (!didMove.current) setSelected(null) }}
        onMouseDown={handleCanvasMouseDown}
      >
        {/* SVG Edges */}
        <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
          {edges.map((edge) => {
            const src = nodes.find((n) => n.id === edge.source)
            const tgt = nodes.find((n) => n.id === edge.target)
            if (!src || !tgt) return null
            const s = getCenter(src), t = getCenter(tgt)
            const mx = (s.x + t.x) / 2
            return (
              <g key={edge.id}>
                <path
                  d={`M${s.x},${s.y} C${mx},${s.y} ${mx},${t.y} ${t.x},${t.y}`}
                  fill="none" stroke="rgba(0,0,0,0.15)" strokeWidth="1.5"
                />
                <circle cx={t.x} cy={t.y} r="3" fill="rgba(0,0,0,0.2)" />
              </g>
            )
          })}
        </svg>

        {/* Nodes */}
        {nodes.map((node) => {
          const nc = NODE_COLORS[node.data.type] || NODE_COLORS.goal
          const isSelected = selected?.id === node.id
          return (
            <div
              key={node.id}
              className={`node-card${isSelected ? ' selected' : ''}`}
              style={{ left: node.position.x + panOffset.x, top: node.position.y + panOffset.y }}
              onMouseDown={(e) => handleNodeMouseDown(e, node)}
              onClick={(e) => handleNodeClick(e, node)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <div style={{ width: 8, height: 8, background: nc.bg, flexShrink: 0 }} />
                <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: nc.bg }}>
                  {nc.label}
                </div>
              </div>
              <div style={{ fontSize: 13, fontWeight: 800, lineHeight: 1.3, color: '#1a1612' }}>{node.data.label}</div>
              <div style={{ fontSize: 12, color: '#6a6560', marginTop: 4, lineHeight: 1.5, fontWeight: 500 }}>{node.data.description}</div>
              {node.data.type === 'question' && (
                <div style={{
                  fontSize: 9, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase',
                  marginTop: 6, display: 'inline-block', padding: '2px 6px',
                  background: node.data.status === 'answered' ? '#065F46' : '#B45309',
                  color: '#fff',
                }}>
                  {node.data.status === 'answered' ? '✓ Answered' : '● Open'}
                </div>
              )}
              {node.data.type === 'finding' && (
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', marginTop: 6, display: 'inline-block', padding: '2px 6px', background: '#065F46', color: '#fff' }}>
                  ✓ Finding
                </div>
              )}
            </div>
          )
        })}

        {/* Research running overlay */}
        {researching && researchLabel && (
          <div style={{
            position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)',
            background: 'var(--black)', color: '#fff',
            padding: '10px 20px', borderRadius: 999,
            display: 'flex', alignItems: 'center', gap: 10,
            boxShadow: '0 8px 0 rgba(0,0,0,0.3), 0 12px 32px rgba(0,0,0,0.4)',
            zIndex: 100, whiteSpace: 'nowrap',
          }}>
            <div className="pulse-dot" />
            <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1px', color: 'var(--orange)', textTransform: 'uppercase' }}>Running</span>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.6)', fontFamily: 'monospace' }}>{researchLabel}</span>
          </div>
        )}

        {/* Feedback popup */}
        {selected && (
          <div className="feedback-popup" style={{
            left: Math.min(popupPos.x, (containerRef.current?.offsetWidth ?? 800) - 268),
            top: Math.min(popupPos.y, (containerRef.current?.offsetHeight ?? 600) - 200),
          }}>
            <button
              onClick={() => setSelected(null)}
              style={{ position: 'absolute', top: 10, right: 12, background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)', cursor: 'pointer', fontSize: 16, lineHeight: 1 }}
            >×</button>
            <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--orange)', marginBottom: 10 }}>
              {selected.data.label}
            </div>
            <textarea
              rows={3} autoFocus value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Tell the AI what to change or explore…"
              style={{ background: 'rgba(255,255,255,0.06)', color: '#fff', fontSize: 12 }}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFeedbackSubmit(false) } }}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
              <button
                disabled={!feedback.trim() || submitting}
                onClick={() => handleFeedbackSubmit(false)}
                style={{
                  flex: 1, fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 700,
                  letterSpacing: '1.5px', textTransform: 'uppercase',
                  background: 'rgba(255,255,255,0.14)', color: '#fff',
                  border: 'none', cursor: 'pointer', padding: 9,
                  borderRadius: 'var(--radius-xs)',
                  boxShadow: '0 4px 0 rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.15)',
                  opacity: (!feedback.trim() || submitting) ? 0.3 : 1,
                }}
              >{submitting ? '…' : 'Update'}</button>
              <button
                disabled={!feedback.trim() || submitting}
                onClick={() => handleFeedbackSubmit(true)}
                style={{
                  flex: 1, fontFamily: 'var(--font-body)', fontSize: 10, fontWeight: 700,
                  letterSpacing: '1.5px', textTransform: 'uppercase',
                  background: 'var(--orange)', color: '#fff',
                  border: 'none', cursor: 'pointer', padding: 9,
                  borderRadius: 'var(--radius-xs)',
                  boxShadow: '0 4px 0 rgba(180,40,0,0.7), inset 0 1px 0 rgba(255,255,255,0.2)',
                  opacity: (!feedback.trim() || submitting) ? 0.3 : 1,
                }}
              >Deep Research</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
