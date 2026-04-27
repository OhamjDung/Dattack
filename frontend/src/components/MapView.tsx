import { useState, useEffect, useRef, useCallback } from 'react'
import type { DattackNode, DattackEdge } from '../types/graph'
import { submitFeedback } from '../api/client'

const NODE_COLORS: Record<string, { bg: string; fg: string; label: string }> = {
  goal:        { bg: '#FF4500', fg: '#fff', label: 'Goal' },
  data_source: { bg: '#1A56DB', fg: '#fff', label: 'Data' },
  technique:   { bg: '#6B21A8', fg: '#fff', label: 'Technique' },
  question:    { bg: '#B45309', fg: '#fff', label: 'Question' },
  finding:     { bg: '#065F46', fg: '#fff', label: 'Finding' },
  insight:     { bg: '#0E7490', fg: '#fff', label: 'Insight' },
}

interface Props {
  nodes: DattackNode[]
  edges: DattackEdge[]
  externalNodes?: DattackNode[]
  externalEdges?: DattackEdge[]
  onApprove: (nodes: DattackNode[], edges: DattackEdge[]) => void
  isAnalysis?: boolean
  hideToolbar?: boolean
  researching?: boolean
  researchWave?: number
  researchLabel?: string
  activeScript?: string
}

export default function MapView({
  nodes: initNodes,
  edges: initEdges,
  externalNodes = [],
  externalEdges = [],
  onApprove,
  isAnalysis = false,
  hideToolbar = false,
  researching = false,
  researchWave = 0,
  researchLabel = '',
  activeScript = '',
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
  const [zoom, setZoom] = useState(1.0)
  const containerRef = useRef<HTMLDivElement>(null)
  const didMove = useRef(false)
  const [glowNodeIds, setGlowNodeIds] = useState<Set<string>>(new Set())
  const [followMode, setFollowMode] = useState(false)
  const minimapRef = useRef<HTMLCanvasElement>(null)
  const minimapXform = useRef({ minX: 0, minY: 0, scale: 1, offX: 0, offY: 0 })

  // Sync initial nodes/edges when parent updates them
  useEffect(() => { setNodes(initNodes) }, [initNodes])
  useEffect(() => { setEdges(initEdges) }, [initEdges])

  // Merge external nodes + glow + follow mode pan
  useEffect(() => {
    if (!externalNodes.length) return
    setNodes((ns) => {
      const ids = new Set(ns.map((n) => n.id))
      const incoming = externalNodes.filter((n) => !ids.has(n.id))
      if (!incoming.length) return ns
      const newIds = incoming.map((n) => n.id)
      setGlowNodeIds((prev) => new Set([...prev, ...newIds]))
      setTimeout(() => {
        setGlowNodeIds((prev) => {
          const next = new Set(prev)
          newIds.forEach((id) => next.delete(id))
          return next
        })
      }, 2500)
      // Follow mode: pan camera to center the newest node
      if (followMode && incoming.length > 0) {
        const target = incoming[incoming.length - 1]
        const cw = containerRef.current?.offsetWidth ?? 800
        const ch = containerRef.current?.offsetHeight ?? 600
        setPanOffset({
          x: cw / (2 * zoom) - target.position.x - 88,
          y: ch / (2 * zoom) - target.position.y - 38,
        })
        setZoom(Math.max(zoom, 0.75))
      }
      return [...ns, ...incoming]
    })
  }, [externalNodes, followMode, zoom])

  useEffect(() => {
    if (!externalEdges.length) return
    setEdges((es) => {
      const ids = new Set(es.map((e) => e.id))
      const incoming = externalEdges.filter((e) => !ids.has(e.id))
      return incoming.length ? [...es, ...incoming] : es
    })
  }, [externalEdges])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const handler = (e: WheelEvent) => {
      e.preventDefault()
      setZoom(z => Math.min(3.0, Math.max(0.25, z - e.deltaY * 0.001)))
    }
    el.addEventListener('wheel', handler, { passive: false })
    return () => el.removeEventListener('wheel', handler)
  }, [])

  function handleNodeMouseDown(e: React.MouseEvent, node: DattackNode) {
    e.stopPropagation()
    didMove.current = false
    setDragging({ id: node.id, startX: e.clientX - node.position.x, startY: e.clientY - node.position.y })
  }

  function handleCanvasMouseDown(e: React.MouseEvent) {
    const tgt = e.target as HTMLElement
    if (tgt.closest('.node-card') || tgt.closest('.feedback-popup')) return
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

  // Minimap draw
  useEffect(() => {
    const canvas = minimapRef.current
    const container = containerRef.current
    if (!canvas || nodes.length === 0) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const MW = canvas.width   // 180
    const MH = canvas.height  // 108

    const xs = nodes.map(n => n.position.x)
    const ys = nodes.map(n => n.position.y)
    const rawMinX = Math.min(...xs) - 40
    const rawMinY = Math.min(...ys) - 40
    const rawMaxX = Math.max(...xs) + 216
    const rawMaxY = Math.max(...ys) + 120

    const scaleX = MW / (rawMaxX - rawMinX)
    const scaleY = MH / (rawMaxY - rawMinY)
    const sc = Math.min(scaleX, scaleY, 0.06)
    const contentW = (rawMaxX - rawMinX) * sc
    const contentH = (rawMaxY - rawMinY) * sc
    const offX = (MW - contentW) / 2
    const offY = (MH - contentH) / 2

    minimapXform.current = { minX: rawMinX, minY: rawMinY, scale: sc, offX, offY }

    ctx.clearRect(0, 0, MW, MH)

    // BG
    ctx.fillStyle = 'rgba(10,8,6,0.88)'
    ctx.fillRect(0, 0, MW, MH)

    // Edges
    ctx.strokeStyle = 'rgba(255,255,255,0.12)'
    ctx.lineWidth = 0.5
    edges.forEach(edge => {
      const src = nodes.find(n => n.id === edge.source)
      const tgt = nodes.find(n => n.id === edge.target)
      if (!src || !tgt) return
      ctx.beginPath()
      ctx.moveTo(offX + (src.position.x + 88 - rawMinX) * sc, offY + (src.position.y + 38 - rawMinY) * sc)
      ctx.lineTo(offX + (tgt.position.x + 88 - rawMinX) * sc, offY + (tgt.position.y + 38 - rawMinY) * sc)
      ctx.stroke()
    })

    // Nodes as dots
    nodes.forEach(node => {
      const nx = offX + (node.position.x + 88 - rawMinX) * sc
      const ny = offY + (node.position.y + 38 - rawMinY) * sc
      const color = NODE_COLORS[node.data.type]?.bg ?? '#888'
      ctx.fillStyle = node.data.status === 'low_confidence' ? 'rgba(120,110,100,0.5)' : color
      ctx.beginPath()
      ctx.arc(nx, ny, node.data.type === 'goal' ? 4 : 2.5, 0, Math.PI * 2)
      ctx.fill()
    })

    // Viewport rect
    if (container) {
      const vpX = offX + (-panOffset.x - rawMinX) * sc
      const vpY = offY + (-panOffset.y - rawMinY) * sc
      const vpW = (container.offsetWidth / zoom) * sc
      const vpH = (container.offsetHeight / zoom) * sc
      ctx.fillStyle = 'rgba(255,255,255,0.06)'
      ctx.fillRect(vpX, vpY, vpW, vpH)
      ctx.strokeStyle = 'rgba(255,255,255,0.35)'
      ctx.lineWidth = 1
      ctx.strokeRect(vpX, vpY, vpW, vpH)
    }
  }, [nodes, edges, panOffset, zoom])

  function handleMinimapClick(e: React.MouseEvent<HTMLCanvasElement>) {
    const canvas = minimapRef.current
    const container = containerRef.current
    if (!canvas || !container) return
    const rect = canvas.getBoundingClientRect()
    const mx = e.clientX - rect.left
    const my = e.clientY - rect.top
    const { minX, minY, scale: sc, offX, offY } = minimapXform.current
    const nodeX = (mx - offX) / sc + minX
    const nodeY = (my - offY) / sc + minY
    setPanOffset({
      x: container.offsetWidth / (2 * zoom) - nodeX,
      y: container.offsetHeight / (2 * zoom) - nodeY,
    })
  }

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
      const res = await submitFeedback(selected.id, feedback, deeper, nodes)
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
  const showToolbar = !isAnalysis && !hideToolbar
  const canvasWidth = isAnalysis ? 'calc(100% - 320px)' : '100%'
  const canvasHeight = (isAnalysis || hideToolbar) ? 'calc(100vh - 64px)' : 'calc(100vh - 64px - 46px)'

  return (
    <div style={{ paddingTop: hideToolbar ? 0 : 64 }}>
      {/* Toolbar */}
      {showToolbar && (
        <div style={{
          padding: '10px 32px',
          borderBottom: '1px solid var(--line)',
          display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
          height: 46,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Zoom controls */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <button onClick={() => setZoom(z => Math.max(0.25, z - 0.1))} style={{ background: 'none', border: '1px solid var(--line)', borderRadius: 4, width: 24, height: 24, cursor: 'pointer', fontSize: 14, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>−</button>
              <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--gray)', minWidth: 36, textAlign: 'center' }}>{Math.round(zoom * 100)}%</span>
              <button onClick={() => setZoom(z => Math.min(3.0, z + 0.1))} style={{ background: 'none', border: '1px solid var(--line)', borderRadius: 4, width: 24, height: 24, cursor: 'pointer', fontSize: 14, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>+</button>
              <button onClick={() => setZoom(1)} style={{ background: 'none', border: '1px solid var(--line)', borderRadius: 4, padding: '0 6px', height: 24, cursor: 'pointer', fontSize: 9, fontWeight: 700, letterSpacing: '1px', color: 'var(--gray)' }}>RESET</button>
            </div>
            {researching ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div className="pulse-dot" />
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'var(--orange)' }}>
                  Researching…
                </span>
                <span style={{ fontSize: 11, color: 'var(--gray)', fontWeight: 500 }}>
                  Wave {researchWave}
                </span>
              </div>
            ) : (
              <button
                className="btn-primary"
                onClick={() => onApprove(nodes, edges)}
                style={{ padding: '10px 24px', fontSize: 12 }}
              >
                Approve Map →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Canvas */}
      <div
        ref={containerRef}
        style={{ position: 'relative', width: canvasWidth, height: canvasHeight, overflow: 'hidden', cursor: cursorStyle }}
        onClick={() => { if (!didMove.current) setSelected(null) }}
        onMouseDown={handleCanvasMouseDown}
      >
        <div style={{ transform: `scale(${zoom})`, transformOrigin: 'top left', width: 5000, height: 5000 }}>
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
          const isLowConf = node.data.status === 'low_confidence'
          const isGlowing = glowNodeIds.has(node.id)
          return (
            <div
              key={node.id}
              className={`node-card${isSelected ? ' selected' : ''}`}
              style={{
                left: node.position.x + panOffset.x,
                top: node.position.y + panOffset.y,
                opacity: isLowConf ? 0.4 : 1,
                filter: isLowConf ? 'grayscale(0.6)' : 'none',
                boxShadow: isGlowing
                  ? '0 0 0 2px #3B82F6, 0 0 24px rgba(59,130,246,0.5), 0 8px 0 rgba(0,0,0,0.25)'
                  : undefined,
                transition: 'box-shadow 0.4s ease',
              }}
              onMouseDown={(e) => handleNodeMouseDown(e, node)}
              onClick={(e) => handleNodeClick(e, node)}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                <div style={{ width: 8, height: 8, background: nc.bg, flexShrink: 0 }} />
                <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: nc.bg }}>
                  {nc.label}
                </div>
                {isLowConf && (
                  <div style={{ fontSize: 8, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', color: '#9a8f85', marginLeft: 'auto' }}>
                    low confidence
                  </div>
                )}
              </div>
              <div style={{ fontSize: 13, fontWeight: 800, lineHeight: 1.3, color: '#1a1612' }}>{node.data.label}</div>
              <div style={{ fontSize: 12, color: '#6a6560', marginTop: 4, lineHeight: 1.5, fontWeight: 500 }}>{node.data.description}</div>
              {node.data.type === 'finding' && (
                <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', marginTop: 6, display: 'inline-block', padding: '2px 6px', background: '#065F46', color: '#fff' }}>
                  ✓ Finding
                </div>
              )}
            </div>
          )
        })}

        </div>{/* end scale wrapper */}

        {/* Follow mode toggle — visible in analysis mode */}
        {isAnalysis && (
          <button
            onClick={() => setFollowMode(f => !f)}
            style={{
              position: 'absolute', top: 14, right: 16, zIndex: 101,
              display: 'flex', alignItems: 'center', gap: 7,
              background: followMode ? 'rgba(59,130,246,0.15)' : 'rgba(255,255,255,0.08)',
              border: `1px solid ${followMode ? 'rgba(59,130,246,0.6)' : 'rgba(255,255,255,0.12)'}`,
              borderRadius: 999,
              padding: '6px 14px',
              cursor: 'pointer',
              color: followMode ? 'rgba(147,197,253,1)' : 'rgba(255,255,255,0.45)',
              fontSize: 10, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase',
              fontFamily: 'var(--font-body)',
              boxShadow: followMode ? '0 0 12px rgba(59,130,246,0.3)' : 'none',
              transition: 'all 0.2s ease',
            }}
          >
            <div style={{
              width: 6, height: 6, borderRadius: '50%',
              background: followMode ? '#3B82F6' : 'rgba(255,255,255,0.3)',
              boxShadow: followMode ? '0 0 6px #3B82F6' : 'none',
            }} />
            {followMode ? 'Following' : 'Follow'}
          </button>
        )}

        {/* Active script overlay */}
        {activeScript && (
          <div style={{
            position: 'absolute', bottom: researching && researchLabel ? 70 : 20, left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(15,23,42,0.92)',
            border: '1px solid rgba(59,130,246,0.5)',
            color: '#fff',
            padding: '8px 18px', borderRadius: 999,
            display: 'flex', alignItems: 'center', gap: 10,
            boxShadow: '0 0 12px rgba(59,130,246,0.3), 0 8px 0 rgba(0,0,0,0.3)',
            zIndex: 100, whiteSpace: 'nowrap',
          }}>
            <div style={{
              width: 8, height: 8, borderRadius: '50%',
              background: '#3B82F6',
              boxShadow: '0 0 8px #3B82F6',
              animation: 'pulse 1s ease-in-out infinite',
            }} />
            <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '1.5px', textTransform: 'uppercase', color: 'rgba(147,197,253,1)' }}>Running</span>
            <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)', fontFamily: 'monospace' }}>{activeScript}</span>
          </div>
        )}

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

        {/* Minimap */}
        {nodes.length > 0 && (
          <div style={{
            position: 'fixed', bottom: 24, left: 24, zIndex: 999,
            borderRadius: 6,
            overflow: 'hidden',
            border: '1px solid rgba(255,255,255,0.1)',
            boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
          }}>
            <div style={{
              background: 'rgba(10,8,6,0.88)',
              padding: '4px 8px',
              fontSize: 8, fontWeight: 800, letterSpacing: '2px',
              textTransform: 'uppercase', color: 'rgba(255,255,255,0.3)',
              borderBottom: '1px solid rgba(255,255,255,0.07)',
            }}>
              Map
            </div>
            <canvas
              ref={minimapRef}
              width={180}
              height={108}
              style={{ display: 'block', cursor: 'crosshair', background: 'rgba(10,8,6,0.88)' }}
              onClick={handleMinimapClick}
            />
          </div>
        )}
      </div>
    </div>
  )
}
