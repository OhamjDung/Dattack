import { useState } from 'react'
import type { DattackNode, DattackEdge } from '../types/graph'
import MapView from './MapView'

const TYPE_COLORS: Record<string, string> = {
  finding: '#065F46',
  insight: '#0E7490',
}

function getConfidenceNum(node: DattackNode): number {
  const meta = node.data.metadata
  if (!meta) return 0.75
  if (typeof meta.confidence === 'number') return meta.confidence
  if (meta.confidence === 'high') return 0.9
  if (meta.confidence === 'medium') return 0.6
  if (meta.confidence === 'low') return 0.3
  return 0.75
}

function confidenceLabel(v: number) {
  if (v >= 0.7) return { label: 'High', color: '#065F46' }
  if (v >= 0.4) return { label: 'Medium', color: '#B45309' }
  return { label: 'Low', color: '#6B21A8' }
}

// Extract "value label" pairs from description text for mini bar charts
function extractStats(text: string): Array<{ label: string; value: number; unit: string }> {
  const out: Array<{ label: string; value: number; unit: string }> = []
  // "44% of customers" / "58% of revenue"
  const pct = /(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?([a-zA-Z][a-zA-Z ]{2,24})/g
  let m
  while ((m = pct.exec(text)) !== null && out.length < 4) {
    out.push({ value: parseFloat(m[1]), label: m[2].trim(), unit: '%' })
  }
  // "1.6x" patterns
  const mult = /(\d+(?:\.\d+)?)x\s+(?:the\s+)?([a-zA-Z][a-zA-Z ]{2,24})/g
  while ((m = mult.exec(text)) !== null && out.length < 4) {
    out.push({ value: parseFloat(m[1]) * 50, label: m[2].trim(), unit: 'x' })
  }
  return out
}

// SVG donut gauge
function ConfidenceGauge({ value, color, size = 80 }: { value: number; color: string; size?: number }) {
  const r = size / 2 - 8
  const cx = size / 2, cy = size / 2
  const circ = 2 * Math.PI * r
  const filled = circ * value
  const pct = Math.round(value * 100)
  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth={7} />
      <circle
        cx={cx} cy={cy} r={r}
        fill="none"
        stroke={color}
        strokeWidth={7}
        strokeDasharray={`${filled} ${circ}`}
        strokeLinecap="round"
        transform={`rotate(-90 ${cx} ${cy})`}
        style={{ transition: 'stroke-dasharray 0.6s ease' }}
      />
      <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle"
        style={{ fontSize: 13, fontWeight: 900, fontFamily: 'var(--font-display)', fill: color }}>
        {pct}%
      </text>
    </svg>
  )
}

// Horizontal bar chart for all findings
function FindingsBarChart({ findings, selectedId, onSelect }: {
  findings: DattackNode[]
  selectedId: string | null
  onSelect: (n: DattackNode) => void
}) {
  if (!findings.length) return null
  const barH = 22
  const gap = 8
  const labelW = 110
  const barW = 160
  const totalH = findings.length * (barH + gap)

  return (
    <svg width={labelW + barW + 48} height={totalH} style={{ display: 'block', overflow: 'visible' }}>
      {findings.map((f, i) => {
        const conf = getConfidenceNum(f)
        const { color } = confidenceLabel(conf)
        const y = i * (barH + gap)
        const isActive = f.id === selectedId
        const truncLabel = f.data.label.length > 14 ? f.data.label.slice(0, 13) + '…' : f.data.label
        return (
          <g key={f.id} style={{ cursor: 'pointer' }} onClick={() => onSelect(f)}>
            <rect x={0} y={y} width={labelW + barW + 40} height={barH} rx={4}
              fill={isActive ? `${color}14` : 'transparent'} />
            <text x={labelW - 6} y={y + barH / 2 + 1} textAnchor="end" dominantBaseline="middle"
              style={{ fontSize: 10, fontWeight: isActive ? 800 : 600, fill: isActive ? color : '#6a6560', fontFamily: 'var(--font-body)' }}>
              {truncLabel}
            </text>
            {/* Track */}
            <rect x={labelW} y={y + 6} width={barW} height={10} rx={5} fill="rgba(0,0,0,0.06)" />
            {/* Fill */}
            <rect x={labelW} y={y + 6} width={barW * conf} height={10} rx={5} fill={color}
              style={{ transition: 'width 0.5s ease' }} />
            {/* Value */}
            <text x={labelW + barW + 6} y={y + barH / 2 + 1} dominantBaseline="middle"
              style={{ fontSize: 9, fontWeight: 700, fill: color, fontFamily: 'var(--font-body)' }}>
              {Math.round(conf * 100)}%
            </text>
          </g>
        )
      })}
    </svg>
  )
}

// Mini stat bars extracted from description
function StatBars({ stats }: { stats: Array<{ label: string; value: number; unit: string }> }) {
  if (!stats.length) return null
  const max = Math.max(...stats.map(s => s.value), 1)
  const barW = 140
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {stats.map((s, i) => (
        <div key={i}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
            <span style={{ fontSize: 9, fontWeight: 700, color: '#6a6560', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              {s.label.slice(0, 20)}
            </span>
            <span style={{ fontSize: 10, fontWeight: 800, color: '#1a1612' }}>
              {s.unit === '%' ? `${s.value}%` : `${(s.value / 50).toFixed(1)}x`}
            </span>
          </div>
          <div style={{ background: 'rgba(0,0,0,0.06)', borderRadius: 4, height: 6, width: barW }}>
            <div style={{
              background: 'linear-gradient(90deg, #065F46, #059669)',
              borderRadius: 4, height: '100%',
              width: `${Math.min((s.value / max) * 100, 100)}%`,
              transition: 'width 0.5s ease',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

interface Props {
  nodes: DattackNode[]
  edges: DattackEdge[]
  streamLog: string[]
}

export default function VizPanel({ nodes, edges, streamLog }: Props) {
  const findings = nodes.filter((n) => n.data.type === 'finding' || n.data.type === 'insight')
  const [selected, setSelected] = useState<DattackNode | null>(findings[0] ?? null)

  const selConf = selected ? getConfidenceNum(selected) : 0
  const selConfStyle = confidenceLabel(selConf)
  const selStats = selected ? extractStats(selected.data.description ?? '') : []
  const selColor = selected ? (TYPE_COLORS[selected.data.type] ?? '#065F46') : '#065F46'

  return (
    <div style={{ paddingTop: 64, height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--bg)' }}>

      {/* Stats strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 10, padding: '14px 24px 0' }}>
        {[
          { label: 'Findings', value: String(findings.filter(n => n.data.type === 'finding').length), sub: 'AI-detected', color: '#065F46' },
          { label: 'Insights', value: String(findings.filter(n => n.data.type === 'insight').length), sub: 'User-guided', color: '#0E7490' },
          { label: 'Avg Confidence', value: findings.length ? `${Math.round(findings.reduce((a, n) => a + getConfidenceNum(n), 0) / findings.length * 100)}%` : '—', sub: 'across all findings', color: '#B45309' },
          { label: 'Total Nodes', value: String(nodes.length), sub: 'in map', color: '#6B21A8' },
        ].map((s, i) => (
          <div key={i} className="clay-card" style={{ padding: '12px 16px' }}>
            <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: s.color, marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 22, fontWeight: 900, color: 'var(--black)', lineHeight: 1, fontFamily: 'var(--font-display)', marginBottom: 3 }}>{s.value}</div>
            <div style={{ fontSize: 10, color: 'var(--gray)', fontWeight: 600 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 12, flex: 1, overflow: 'hidden', padding: '12px 24px 20px' }}>

        {/* Left: finding list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, overflowY: 'auto', paddingRight: 4 }}>
          {findings.length === 0 && (
            <div style={{ fontSize: 13, color: 'var(--gray)', fontWeight: 500, padding: '20px 0' }}>
              No findings generated yet.
            </div>
          )}
          {findings.map((f) => {
            const tagColor = TYPE_COLORS[f.data.type] ?? '#065F46'
            const conf = getConfidenceNum(f)
            const confStyle = confidenceLabel(conf)
            const isActive = selected?.id === f.id
            return (
              <div
                key={f.id}
                onClick={() => setSelected(f)}
                className="clay-card"
                style={{
                  padding: '14px 16px', cursor: 'pointer',
                  borderLeft: `4px solid ${tagColor}`,
                  boxShadow: isActive
                    ? `0 8px 0 0 ${tagColor}55, 0 12px 28px ${tagColor}22, inset 0 1.5px 0 rgba(255,255,255,0.8)`
                    : undefined,
                  transform: isActive ? 'translateY(-2px)' : undefined,
                  transition: 'transform .15s, box-shadow .15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
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
                <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--black)', marginBottom: 5, lineHeight: 1.3 }}>
                  {f.data.label}
                </div>
                <div style={{ fontSize: 11, color: 'var(--gray)', lineHeight: 1.4, fontWeight: 500, marginBottom: 8 }}>
                  {f.data.description}
                </div>
                {/* Mini confidence bar */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <div style={{ flex: 1, background: 'rgba(0,0,0,0.06)', borderRadius: 4, height: 4 }}>
                    <div style={{
                      width: `${Math.round(conf * 100)}%`, height: '100%',
                      background: confStyle.color, borderRadius: 4,
                      transition: 'width 0.4s ease',
                    }} />
                  </div>
                  <span style={{ fontSize: 9, fontWeight: 800, color: confStyle.color, minWidth: 28 }}>
                    {Math.round(conf * 100)}%
                  </span>
                </div>
              </div>
            )
          })}

          {/* Stream log */}
          {streamLog.length > 0 && (
            <div style={{ marginTop: 6, background: 'rgba(0,0,0,0.03)', borderRadius: 8, padding: '10px 12px' }}>
              <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 8 }}>
                Analysis Log
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {streamLog.map((entry, i) => (
                  <div key={i} style={{
                    fontSize: 10, fontWeight: 500, color: entry.startsWith('✓') ? '#065F46' : 'var(--gray)',
                    lineHeight: 1.5, fontFamily: 'monospace',
                  }}>
                    {entry}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right: charts + map */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, overflow: 'hidden' }}>

          {/* Charts row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, flexShrink: 0 }}>

            {/* Chart 1: All findings confidence bar chart */}
            <div className="clay-card" style={{ padding: '16px 20px', overflow: 'hidden' }}>
              <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 12 }}>
                Confidence by Finding
              </div>
              {findings.length > 0 ? (
                <div style={{ overflowY: 'auto', maxHeight: 180 }}>
                  <FindingsBarChart
                    findings={findings}
                    selectedId={selected?.id ?? null}
                    onSelect={setSelected}
                  />
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--gray)', fontStyle: 'italic' }}>No findings yet.</div>
              )}
            </div>

            {/* Chart 2: Selected finding detail + gauge */}
            <div className="clay-card" style={{ padding: '16px 20px' }}>
              <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 12 }}>
                Selected Finding
              </div>
              {selected ? (
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                  <div style={{ flexShrink: 0 }}>
                    <ConfidenceGauge value={selConf} color={selConfStyle.color} size={90} />
                    <div style={{ textAlign: 'center', marginTop: 4 }}>
                      <span style={{
                        fontSize: 8, fontWeight: 800, letterSpacing: '1px', textTransform: 'uppercase',
                        background: `${selConfStyle.color}18`, color: selConfStyle.color,
                        padding: '2px 8px', borderRadius: 999,
                      }}>
                        {selConfStyle.label} Confidence
                      </span>
                    </div>
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, fontWeight: 800, color: selColor, marginBottom: 4, lineHeight: 1.3 }}>
                      {selected.data.label}
                    </div>
                    {selStats.length > 0 ? (
                      <StatBars stats={selStats} />
                    ) : (
                      <div style={{ fontSize: 10, color: 'var(--gray)', lineHeight: 1.5, fontWeight: 500 }}>
                        {selected.data.description}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div style={{ fontSize: 12, color: 'var(--gray)', fontStyle: 'italic' }}>Select a finding.</div>
              )}
            </div>
          </div>

          {/* Map */}
          <div style={{ flex: 1, position: 'relative', overflow: 'hidden', borderRadius: 16, border: '1px solid var(--line)', minHeight: 0 }}>
            <MapView
              nodes={nodes}
              edges={edges}
              onApprove={() => {}}
              hideToolbar
            />
          </div>
        </div>
      </div>
    </div>
  )
}
