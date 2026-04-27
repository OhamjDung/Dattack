import { useState } from 'react'
import type { DattackNode, DattackEdge } from '../types/graph'

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

// Extract ALL percentages from text
function extractPercentages(text: string): Array<{ label: string; value: number }> {
  const out: Array<{ label: string; value: number }> = []
  const rx = /(\d+(?:\.\d+)?)\s*%/g
  let m
  while ((m = rx.exec(text)) !== null && out.length < 6) {
    const val = parseFloat(m[1])
    if (val < 0.1 || val > 100) continue
    // grab surrounding context as label
    const before = text.slice(Math.max(0, m.index - 50), m.index).trim()
    const words = before.split(/\s+/).slice(-4).join(' ')
    out.push({ label: words || `${val}%`, value: val })
  }
  return out
}

// Extract "X ... compared to Y" or "X vs Y" (words can be between)
function extractComparisons(text: string): Array<{ a: number; aLabel: string; b: number; bLabel: string }> {
  const out: Array<{ a: number; aLabel: string; b: number; bLabel: string }> = []
  // "average of 6.20 malnutrition cases compared to 14.55"
  const rx = /(\d+(?:\.\d+)?)\s+([\w\s]{0,40}?)(?:compared to|versus|vs\.?)\s+(\d+(?:\.\d+)?)/gi
  let m
  while ((m = rx.exec(text)) !== null && out.length < 3) {
    out.push({
      a: parseFloat(m[1]), aLabel: m[2].trim().slice(0, 24) || 'Group A',
      b: parseFloat(m[3]), bLabel: 'vs',
    })
  }
  return out
}

// Extract r-values: "r=0.71", "r-value of 0.71", "r = 0.71", "(r=0.71)"
function extractRValues(text: string): Array<{ r: number; context: string }> {
  const out: Array<{ r: number; context: string }> = []
  // matches: r=0.71 / r = 0.71 / r-value of 0.71 / r-value: 0.71
  const rx = /r(?:[=\s\-](?:value)?(?:\s+of)?(?:\s*[:=])?\s*)(\d+(?:\.\d+)?)/gi
  let m
  while ((m = rx.exec(text)) !== null && out.length < 5) {
    const r = parseFloat(m[1])
    if (r < 0 || r > 1) continue
    const ctx = text.slice(Math.max(0, m.index - 30), m.index + m[0].length + 30).trim()
    out.push({ r, context: ctx.slice(0, 40) })
  }
  return out
}

// Detect finding "type" from text
type ChartType = 'correlation' | 'comparison' | 'percentage' | 'text'
function detectChartType(desc: string): ChartType {
  const t = desc.toLowerCase()
  const rVals = extractRValues(desc)
  if (rVals.length > 0) return 'correlation'
  const comps = extractComparisons(desc)
  if (comps.length > 0) return 'comparison'
  const pcts = extractPercentages(desc)
  if (pcts.length > 0) return 'percentage'
  if (t.includes('correlat') || t.includes('r=')) return 'correlation'
  return 'text'
}

// ---- Chart components ----

function CorrelationBars({ rVals, color }: { rVals: Array<{ r: number; context: string }>; color: string }) {
  const W = 180, barH = 20, gap = 10
  const totalH = rVals.length * (barH + gap) + 24
  return (
    <svg width={W + 100} height={totalH} style={{ display: 'block', overflow: 'visible' }}>
      <text x={0} y={12} style={{ fontSize: 9, fontWeight: 800, fill: '#9a8f85', letterSpacing: '1.5px', textTransform: 'uppercase', fontFamily: 'var(--font-body)' }}>
        Correlation strength
      </text>
      {rVals.map((d, i) => {
        const y = 20 + i * (barH + gap)
        const fillW = W * d.r
        const col = d.r >= 0.7 ? color : d.r >= 0.5 ? '#B45309' : '#6B21A8'
        return (
          <g key={i}>
            <rect x={0} y={y} width={W} height={barH} rx={4} fill="rgba(0,0,0,0.06)" />
            <rect x={0} y={y} width={fillW} height={barH} rx={4} fill={col}
              style={{ transition: 'width 0.6s ease' }} />
            <text x={fillW + 6} y={y + barH / 2 + 1} dominantBaseline="middle"
              style={{ fontSize: 10, fontWeight: 800, fill: col, fontFamily: 'var(--font-body)' }}>
              r={d.r.toFixed(2)}
            </text>
            <text x={0} y={y + barH + gap - 2}
              style={{ fontSize: 9, fill: '#6a6560', fontFamily: 'var(--font-body)' }}>
              {d.context.slice(0, 45)}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function ComparisonBars({ comps, color }: { comps: Array<{ a: number; aLabel: string; b: number; bLabel: string }>; color: string }) {
  const comp = comps[0]
  const maxV = Math.max(comp.a, comp.b, 0.01)
  const W = 220, barH = 28
  const ratio = comp.b > 0 ? (comp.b / comp.a).toFixed(1) : null
  return (
    <svg width={W + 80} height={110} style={{ display: 'block', overflow: 'visible' }}>
      <text x={0} y={12} style={{ fontSize: 9, fontWeight: 800, fill: '#9a8f85', letterSpacing: '1.5px', textTransform: 'uppercase', fontFamily: 'var(--font-body)' }}>
        Comparison
      </text>
      {/* Bar A */}
      <text x={0} y={30} style={{ fontSize: 9, fontWeight: 600, fill: '#6a6560', fontFamily: 'var(--font-body)' }}>High</text>
      <rect x={40} y={16} width={W} height={barH} rx={5} fill="rgba(0,0,0,0.06)" />
      <rect x={40} y={16} width={W * (comp.a / maxV)} height={barH} rx={5} fill={color}
        style={{ transition: 'width 0.6s ease' }} />
      <text x={44 + W * (comp.a / maxV)} y={33} dominantBaseline="middle"
        style={{ fontSize: 11, fontWeight: 800, fill: color, fontFamily: 'var(--font-body)' }}>{comp.a}</text>
      {/* Bar B */}
      <text x={0} y={73} style={{ fontSize: 9, fontWeight: 600, fill: '#6a6560', fontFamily: 'var(--font-body)' }}>Low</text>
      <rect x={40} y={58} width={W} height={barH} rx={5} fill="rgba(0,0,0,0.06)" />
      <rect x={40} y={58} width={W * (comp.b / maxV)} height={barH} rx={5} fill="#B45309"
        style={{ transition: 'width 0.6s ease' }} />
      <text x={44 + W * (comp.b / maxV)} y={75} dominantBaseline="middle"
        style={{ fontSize: 11, fontWeight: 800, fill: '#B45309', fontFamily: 'var(--font-body)' }}>{comp.b}</text>
      {ratio && (
        <text x={40} y={105}
          style={{ fontSize: 10, fill: '#9a8f85', fontFamily: 'var(--font-body)' }}>
          {`Low group is ${ratio}× higher`}
        </text>
      )}
    </svg>
  )
}

function PctBars({ pcts, color }: { pcts: Array<{ label: string; value: number }>; color: string }) {
  const maxV = Math.max(...pcts.map(p => p.value), 1)
  const W = 200, barH = 22, gap = 8
  const totalH = pcts.length * (barH + gap) + 24
  return (
    <svg width={W + 80} height={totalH} style={{ display: 'block', overflow: 'visible' }}>
      <text x={0} y={12} style={{ fontSize: 9, fontWeight: 800, fill: '#9a8f85', letterSpacing: '1.5px', textTransform: 'uppercase', fontFamily: 'var(--font-body)' }}>
        Key percentages
      </text>
      {pcts.map((p, i) => {
        const y = 20 + i * (barH + gap)
        const fillW = W * (p.value / maxV)
        return (
          <g key={i}>
            <rect x={0} y={y} width={W} height={barH} rx={4} fill="rgba(0,0,0,0.06)" />
            <rect x={0} y={y} width={fillW} height={barH} rx={4} fill={color}
              style={{ transition: 'width 0.6s ease' }} />
            <text x={fillW + 5} y={y + barH / 2 + 1} dominantBaseline="middle"
              style={{ fontSize: 10, fontWeight: 800, fill: color, fontFamily: 'var(--font-body)' }}>{p.value}%</text>
            <text x={0} y={y + barH + gap - 2}
              style={{ fontSize: 9, fill: '#6a6560', fontFamily: 'var(--font-body)' }}>
              {p.label.slice(0, 50)}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

function FindingChart({ node, color }: { node: DattackNode; color: string }) {
  const desc = node.data.description ?? ''
  const chartType = detectChartType(desc)

  if (chartType === 'correlation') {
    const rVals = extractRValues(desc)
    if (rVals.length > 0) return <CorrelationBars rVals={rVals} color={color} />
    // has "correlation" text but no r= found — fall to text
  }
  if (chartType === 'comparison') {
    const comps = extractComparisons(desc)
    if (comps.length > 0) return <ComparisonBars comps={comps} color={color} />
  }
  if (chartType === 'percentage') {
    const pcts = extractPercentages(desc)
    if (pcts.length > 0) return <PctBars pcts={pcts} color={color} />
  }

  // Text fallback — styled quote block
  return (
    <div style={{
      background: `${color}08`, border: `1px solid ${color}22`,
      borderRadius: 8, padding: '12px 16px',
    }}>
      <div style={{ fontSize: 11, color: '#4a4540', lineHeight: 1.7, fontWeight: 500 }}>
        {desc || 'No additional data available.'}
      </div>
    </div>
  )
}

// Auto-group findings by topic keywords
function groupFindings(findings: DattackNode[]): Array<{ group: string; nodes: DattackNode[] }> {
  const groups: Record<string, DattackNode[]> = {}
  for (const f of findings) {
    const text = (f.data.label + ' ' + (f.data.description ?? '')).toLowerCase()
    let g = 'General'
    if (text.match(/correlat|r=|r-value|scatter/)) g = 'Correlations'
    else if (text.match(/food|nutriti|caloric|protein|stunting|wasting|underweight/)) g = 'Nutrition'
    else if (text.match(/region|east|west|north|south|geographic|area/)) g = 'Regional'
    else if (text.match(/income|economic|wealth|access|healthcare|water/)) g = 'Socioeconomic'
    else if (text.match(/segment|concentrat|pareto|top|bottom|rank/)) g = 'Distribution'
    else if (text.match(/time|season|temporal|trend|year|month|quarter/)) g = 'Temporal'
    if (!groups[g]) groups[g] = []
    groups[g].push(f)
  }
  const result: Array<{ group: string; nodes: DattackNode[] }> = []
  for (const [g, nodes] of Object.entries(groups)) {
    if (nodes.length > 0) result.push({ group: g, nodes })
  }
  result.sort((a, b) => b.nodes.length - a.nodes.length)
  return result
}

interface Props {
  nodes: DattackNode[]
  edges: DattackEdge[]
  streamLog: string[]
}

export default function VizPanel({ nodes, edges: _edges, streamLog }: Props) {
  const findings = nodes.filter((n) => n.data.type === 'finding' || n.data.type === 'insight')
  const [selected, setSelected] = useState<DattackNode | null>(findings[0] ?? null)

  const selConf = selected ? getConfidenceNum(selected) : 0
  const selConfStyle = confidenceLabel(selConf)
  const selColor = selected ? (TYPE_COLORS[selected.data.type] ?? '#065F46') : '#065F46'
  const groups = groupFindings(findings)

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
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 12, flex: 1, overflow: 'hidden', padding: '12px 24px 20px' }}>

        {/* Left: grouped finding list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, overflowY: 'auto', paddingRight: 4 }}>
          {findings.length === 0 && (
            <div style={{ fontSize: 13, color: 'var(--gray)', fontWeight: 500, padding: '20px 0' }}>No findings generated yet.</div>
          )}
          {groups.map(({ group, nodes: gNodes }) => (
            <div key={group}>
              <div style={{
                fontSize: 8, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase',
                color: 'var(--gray)', padding: '8px 0 4px',
                borderBottom: '1px solid var(--line)', marginBottom: 4,
              }}>
                {group} · {gNodes.length}
              </div>
              {gNodes.map((f) => {
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
                      padding: '12px 14px', cursor: 'pointer', marginBottom: 6,
                      borderLeft: `4px solid ${tagColor}`,
                      boxShadow: isActive
                        ? `0 8px 0 0 ${tagColor}55, 0 12px 28px ${tagColor}22, inset 0 1.5px 0 rgba(255,255,255,0.8)`
                        : undefined,
                      transform: isActive ? 'translateY(-2px)' : undefined,
                      transition: 'transform .15s, box-shadow .15s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 5, gap: 6 }}>
                      <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--black)', lineHeight: 1.3, flex: 1 }}>
                        {f.data.label}
                      </span>
                      <span style={{
                        fontSize: 8, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase',
                        background: `${confStyle.color}18`, color: confStyle.color,
                        padding: '2px 7px', borderRadius: 999, flexShrink: 0,
                      }}>
                        {confStyle.label}
                      </span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, background: 'rgba(0,0,0,0.06)', borderRadius: 4, height: 3 }}>
                        <div style={{
                          width: `${Math.round(conf * 100)}%`, height: '100%',
                          background: confStyle.color, borderRadius: 4, transition: 'width 0.4s ease',
                        }} />
                      </div>
                      <span style={{ fontSize: 8, fontWeight: 800, color: confStyle.color, minWidth: 24 }}>
                        {Math.round(conf * 100)}%
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          ))}

          {/* Stream log */}
          {streamLog.length > 0 && (
            <div style={{ marginTop: 6, background: 'rgba(0,0,0,0.03)', borderRadius: 8, padding: '10px 12px' }}>
              <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 8 }}>
                Analysis Log
              </div>
              {streamLog.map((entry, i) => (
                <div key={i} style={{
                  fontSize: 10, fontWeight: 500, lineHeight: 1.5, fontFamily: 'monospace',
                  color: entry.startsWith('✓') ? '#065F46' : 'var(--gray)',
                }}>
                  {entry}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: selected finding detail */}
        <div style={{ overflowY: 'auto' }}>
          {selected ? (
            <div className="clay-card" style={{ padding: '24px 28px' }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: selColor }}>
                  {selected.data.type === 'insight' ? 'Insight' : 'Finding'}
                </span>
                <span style={{
                  fontSize: 8, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase',
                  background: `${selConfStyle.color}18`, color: selConfStyle.color,
                  padding: '2px 8px', borderRadius: 999,
                }}>
                  {selConfStyle.label} · {Math.round(selConf * 100)}%
                </span>
              </div>

              {/* Title */}
              <div style={{ fontSize: 22, fontWeight: 900, color: 'var(--black)', lineHeight: 1.25, marginBottom: 12, fontFamily: 'var(--font-display)' }}>
                {selected.data.label}
              </div>

              {/* Description */}
              <div style={{ fontSize: 13, color: '#4a4540', lineHeight: 1.7, fontWeight: 500, marginBottom: 24, paddingBottom: 24, borderBottom: '1px solid var(--line)' }}>
                {selected.data.description}
              </div>

              {/* Chart */}
              <div>
                <div style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 14 }}>
                  Data Visualization
                </div>
                <FindingChart node={selected} color={selColor} />
              </div>
            </div>
          ) : (
            <div style={{ fontSize: 13, color: 'var(--gray)', fontStyle: 'italic', padding: 20 }}>Select a finding from the left.</div>
          )}
        </div>
      </div>
    </div>
  )
}
