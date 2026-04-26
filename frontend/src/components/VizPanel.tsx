import { useState } from 'react'
import type { DattackNode, DattackEdge } from '../types/graph'
import MapView from './MapView'

const TYPE_COLORS: Record<string, string> = {
  finding: '#065F46',
  insight: '#0E7490',
}

const CONFIDENCE_LABELS: Record<string, { label: string; color: string }> = {
  high:   { label: 'High',   color: '#065F46' },
  medium: { label: 'Medium', color: '#B45309' },
  low:    { label: 'Low',    color: '#6B21A8' },
}

function getConfidence(node: DattackNode): string {
  const meta = node.data.metadata
  if (meta && typeof meta.confidence === 'string') return meta.confidence
  if (meta && typeof meta.confidence === 'number') {
    if (meta.confidence >= 0.7) return 'high'
    if (meta.confidence >= 0.4) return 'medium'
    return 'low'
  }
  return 'high'
}

interface Props {
  nodes: DattackNode[]
  edges: DattackEdge[]
  streamLog: string[]
}

export default function VizPanel({ nodes, edges, streamLog }: Props) {
  const findings = nodes.filter((n) => n.data.type === 'finding' || n.data.type === 'insight')
  const [selected, setSelected] = useState<DattackNode | null>(findings[0] ?? null)

  return (
    <div style={{ paddingTop: 64, height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Stats strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, padding: '16px 28px 16px' }}>
        {[
          { label: 'Findings', value: String(findings.filter(n => n.data.type === 'finding').length), sub: 'AI-detected' },
          { label: 'Insights', value: String(findings.filter(n => n.data.type === 'insight').length), sub: 'User-guided' },
          { label: 'Total Nodes', value: String(nodes.length), sub: 'in map' },
        ].map((s, i) => (
          <div key={i} className="clay-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 26, fontWeight: 900, color: 'var(--black)', lineHeight: 1, fontFamily: 'var(--font-display)', marginBottom: 4 }}>{s.value}</div>
            <div style={{ fontSize: 11, color: 'var(--gray)', fontWeight: 600 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, flex: 1, overflow: 'hidden', padding: '0 28px 24px' }}>
        {/* Left: finding list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto', paddingRight: 4 }}>
          {findings.length === 0 && (
            <div style={{ fontSize: 13, color: 'var(--gray)', fontWeight: 500, padding: '20px 0' }}>
              No findings generated yet.
            </div>
          )}
          {findings.map((f) => {
            const tagColor = TYPE_COLORS[f.data.type] ?? '#065F46'
            const conf = getConfidence(f)
            const confStyle = CONFIDENCE_LABELS[conf] ?? CONFIDENCE_LABELS.high
            const isActive = selected?.id === f.id
            return (
              <div
                key={f.id}
                onClick={() => setSelected(f)}
                className="clay-card"
                style={{
                  padding: '16px 18px', cursor: 'pointer',
                  borderLeft: `4px solid ${tagColor}`,
                  boxShadow: isActive
                    ? `0 8px 0 0 ${tagColor}55, 0 12px 28px ${tagColor}22, inset 0 1.5px 0 rgba(255,255,255,0.8)`
                    : undefined,
                  transform: isActive ? 'translateY(-2px)' : undefined,
                  transition: 'transform .15s, box-shadow .15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: tagColor }}>
                    {f.data.type === 'insight' ? 'Insight' : 'Finding'}
                  </span>
                  <span style={{
                    fontSize: 9, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase',
                    background: `${confStyle.color}18`, color: confStyle.color,
                    padding: '2px 8px', borderRadius: 999,
                  }}>
                    {confStyle.label}
                  </span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--black)', marginBottom: 6, lineHeight: 1.3 }}>
                  {f.data.label}
                </div>
                <div style={{ fontSize: 12, color: 'var(--gray)', lineHeight: 1.5, fontWeight: 500 }}>
                  {f.data.description}
                </div>
              </div>
            )
          })}

          {/* Stream log */}
          {streamLog.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 8 }}>
                Analysis Log
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                {streamLog.map((entry, i) => (
                  <div key={i} style={{
                    fontSize: 11, fontWeight: 500, color: entry.startsWith('✓') ? '#065F46' : 'var(--gray)',
                    lineHeight: 1.5, fontFamily: 'monospace',
                  }}>
                    {entry}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: map */}
        <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 16, border: '1px solid var(--line)' }}>
          <MapView
            nodes={nodes}
            edges={edges}
            onApprove={() => {}}
            hideToolbar
          />
        </div>
      </div>
    </div>
  )
}
