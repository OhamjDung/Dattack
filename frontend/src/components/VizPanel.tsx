import { useState } from 'react'

const SEVERITY_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  critical: { bg: '#FEE2E2', color: '#991B1B', label: 'Critical' },
  high:     { bg: '#FEF3C7', color: '#92400E', label: 'High' },
  medium:   { bg: '#EDE9FE', color: '#5B21B6', label: 'Medium' },
  resolved: { bg: '#D1FAE5', color: '#065F46', label: 'Resolved' },
}

// ── Chart primitives ─────────────────────────────────────────────

function FunnelViz() {
  const [hovered, setHovered] = useState<number | null>(null)
  const steps = [
    { label: 'Sign Up', pct: 100 },
    { label: 'Profile', pct: 94 },
    { label: 'Connect Data', pct: 59 },
    { label: 'First Query', pct: 41 },
    { label: 'Activated', pct: 38 },
  ]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 4 }}>
        Onboarding Funnel — Post v2.4
      </div>
      {steps.map((s, i) => (
        <div key={i} style={{ cursor: 'pointer' }}
          onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
            <span style={{ fontSize: 13, fontWeight: hovered === i ? 800 : 600, color: i === 2 ? '#FF4500' : 'var(--black)' }}>{s.label}</span>
            <span style={{ fontSize: 13, fontWeight: 800, color: i === 2 ? '#FF4500' : 'var(--black)' }}>{s.pct}%</span>
          </div>
          <div style={{ height: 12, borderRadius: 6, background: 'rgba(0,0,0,0.07)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${s.pct}%`, borderRadius: 6,
              background: i === 2 ? '#FF4500' : i >= 3 ? '#FF450066' : '#1A56DB',
              transition: 'width .6s cubic-bezier(.22,1,.36,1)',
            }} />
          </div>
          {i === 2 && <div style={{ fontSize: 11, color: '#FF4500', fontWeight: 700, marginTop: 4 }}>⚠ 38% error rate — regression detected</div>}
        </div>
      ))}
      <div style={{ background: 'rgba(255,69,0,0.08)', borderRadius: 12, padding: '14px 16px', borderLeft: '3px solid #FF4500' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#FF4500', marginBottom: 4 }}>Drop from v2.3 → v2.4</div>
        <div style={{ fontSize: 13, color: 'var(--black)', fontWeight: 500 }}>Step 3 completion fell from <strong>91% → 59%</strong> overnight on Jun 28.</div>
      </div>
    </div>
  )
}

function ChannelViz() {
  const [hovered, setHovered] = useState<number | null>(null)
  const channels = [
    { label: 'Direct', after: 66, color: '#1A56DB' },
    { label: 'Partner', after: 97, color: '#6B21A8' },
    { label: 'Inbound', after: 91, color: '#065F46' },
    { label: 'Enterprise', after: 99, color: '#B45309' },
  ]
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)' }}>
        Revenue Index by Channel — Jul vs Jun (Jun = 100)
      </div>
      {channels.map((ch, i) => (
        <div key={i} style={{ cursor: 'pointer' }}
          onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700 }}>{ch.label}</span>
            <span style={{ fontSize: 13, fontWeight: 800, color: ch.after < 80 ? '#FF4500' : 'var(--black)' }}>{ch.after}</span>
          </div>
          <div style={{ height: 28, borderRadius: 8, background: 'rgba(0,0,0,0.06)', overflow: 'hidden', position: 'relative' }}>
            <div style={{ position: 'absolute', height: '100%', width: '100%', background: `${ch.color}22`, borderRadius: 8 }} />
            <div style={{
              height: '100%', width: `${ch.after}%`, borderRadius: 8,
              background: ch.color, opacity: hovered === i ? 1 : 0.8,
              transition: 'width .6s cubic-bezier(.22,1,.36,1), opacity .15s',
            }} />
          </div>
          {hovered === i && <div style={{ fontSize: 11, color: 'var(--gray)', marginTop: 4, fontWeight: 600 }}>−{100 - ch.after}% vs prior month</div>}
        </div>
      ))}
    </div>
  )
}

function CohortViz() {
  const [hovered, setHovered] = useState<number | null>(null)
  const cohorts = [
    { label: 'Apr', ltv: 142 }, { label: 'May', ltv: 151 }, { label: 'Jun', ltv: 148 },
    { label: 'Jul', ltv: 109 }, { label: 'Aug', ltv: 118 }, { label: 'Sep', ltv: 131 },
  ]
  const max = Math.max(...cohorts.map((c) => c.ltv))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)' }}>
        6-Month LTV by Acquisition Cohort ($)
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, height: 140 }}>
        {cohorts.map((c, i) => (
          <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, cursor: 'pointer' }}
            onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
            {hovered === i && (
              <div style={{ fontSize: 12, fontWeight: 800, color: c.label === 'Jul' ? '#FF4500' : '#6B21A8', background: 'var(--white)', padding: '3px 8px', borderRadius: 6, boxShadow: '0 3px 0 rgba(0,0,0,0.12)', whiteSpace: 'nowrap' }}>
                ${c.ltv}
              </div>
            )}
            <div style={{
              width: '100%', height: `${(c.ltv / max) * 110}px`,
              background: c.label === 'Jul' ? '#FF4500' : hovered === i ? '#6B21A8' : '#6B21A8BB',
              borderRadius: '8px 8px 4px 4px',
              transition: 'height .6s cubic-bezier(.22,1,.36,1)',
            }} />
            <span style={{ fontSize: 11, fontWeight: 700, color: c.label === 'Jul' ? '#FF4500' : 'var(--gray)' }}>{c.label}</span>
          </div>
        ))}
      </div>
      <div style={{ background: 'rgba(107,33,168,0.08)', borderRadius: 12, padding: '14px 16px', borderLeft: '3px solid #6B21A8' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#6B21A8', marginBottom: 4 }}>July anomaly</div>
        <div style={{ fontSize: 13, color: 'var(--black)', fontWeight: 500 }}>
          July LTV ($109) is <strong>28% below</strong> the Apr–Jun average ($147). 7-day churn rate: 62% vs 22% norm.
        </div>
      </div>
    </div>
  )
}

function RetentionViz() {
  const [hovered, setHovered] = useState<number | null>(null)
  const data = [
    { label: 'Jul', val: 70 }, { label: 'Aug', val: 73 }, { label: 'Sep', val: 68 },
    { label: 'Oct', val: 79 }, { label: 'Nov', val: 82 }, { label: 'Dec', val: 88 },
  ]
  const max = Math.max(...data.map((d) => d.val))
  const min = Math.min(...data.map((d) => d.val))
  const W = 320, H = 120, pad = 16
  const xs = data.map((_, i) => pad + (i / (data.length - 1)) * (W - pad * 2))
  const ys = data.map((d) => H - pad - ((d.val - min) / (max - min)) * (H - pad * 2))
  const pathD = xs.map((x, i) => `${i === 0 ? 'M' : 'L'}${x},${ys[i]}`).join(' ')
  const areaD = `${pathD} L${xs[xs.length - 1]},${H} L${xs[0]},${H} Z`
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)' }}>
        Monthly Retention Rate (%)
      </div>
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="retGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#065F46" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#065F46" stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <line x1={xs[2] + (xs[3] - xs[2]) / 2} y1={0} x2={xs[2] + (xs[3] - xs[2]) / 2} y2={H}
          stroke="#FF4500" strokeWidth="1.5" strokeDasharray="4,3" opacity="0.5" />
        <text x={xs[2] + (xs[3] - xs[2]) / 2 + 4} y={14} fontSize="9" fill="#FF4500" fontWeight="700" fontFamily="Space Grotesk">Hotfix</text>
        <path d={areaD} fill="url(#retGrad)" />
        <path d={pathD} fill="none" stroke="#065F46" strokeWidth="2.5" strokeLinejoin="round" />
        {xs.map((x, i) => (
          <circle key={i} cx={x} cy={ys[i]} r={hovered === i ? 6 : 4}
            fill={hovered === i ? '#065F46' : 'var(--white)'} stroke="#065F46" strokeWidth="2.5"
            style={{ cursor: 'pointer', transition: 'r .1s' }}
            onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)} />
        ))}
        {hovered !== null && (
          <text x={xs[hovered]} y={ys[hovered] - 12} textAnchor="middle" fontSize="12" fontWeight="800" fill="#065F46" fontFamily="Space Grotesk">
            {data[hovered].val}%
          </text>
        )}
      </svg>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        {data.map((d, i) => (
          <span key={i} style={{ fontSize: 11, fontWeight: hovered === i ? 800 : 600, color: hovered === i ? '#065F46' : 'var(--gray)' }}>{d.label}</span>
        ))}
      </div>
      <div style={{ background: 'rgba(6,95,70,0.08)', borderRadius: 12, padding: '14px 16px', borderLeft: '3px solid #065F46' }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#065F46', marginBottom: 4 }}>Above baseline</div>
        <div style={{ fontSize: 13, color: 'var(--black)', fontWeight: 500 }}>Dec retention (88%) is <strong>+6pp above</strong> pre-regression baseline (82%). Recovery complete.</div>
      </div>
    </div>
  )
}

function SegmentViz() {
  const [hovered, setHovered] = useState<number | null>(null)
  const segs = [
    { label: 'SMB Self-Serve', churn: 47, color: '#FF4500' },
    { label: 'Mid-Market', churn: 28, color: '#B45309' },
    { label: 'Enterprise CSM', churn: 15, color: '#065F46' },
    { label: 'Partner-Led', churn: 18, color: '#1A56DB' },
  ]
  const max = Math.max(...segs.map((s) => s.churn))
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)' }}>
        30-Day Churn Rate by Segment — Jul 2024
      </div>
      {segs.map((s, i) => (
        <div key={i} style={{ cursor: 'pointer' }}
          onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: hovered === i ? s.color : 'var(--black)' }}>{s.label}</span>
            <span style={{ fontSize: 13, fontWeight: 800, color: s.color }}>{s.churn}%</span>
          </div>
          <div style={{ height: 24, borderRadius: 8, background: 'rgba(0,0,0,0.06)', overflow: 'hidden' }}>
            <div style={{
              height: '100%', width: `${(s.churn / max) * 100}%`,
              background: s.color, borderRadius: 8,
              opacity: hovered === i ? 1 : 0.75,
              transition: 'width .6s cubic-bezier(.22,1,.36,1), opacity .15s',
            }} />
          </div>
        </div>
      ))}
    </div>
  )
}

// ── Findings data ──────────────────────────────────────────────

const FINDINGS = [
  {
    id: 'f1', tag: 'ROOT CAUSE', tagColor: '#FF4500', severity: 'critical',
    title: 'v2.4 Onboarding Regression',
    summary: 'Jun 28 deploy broke step 3 of onboarding. 41% of new users abandoned before activation.',
    detail: 'The v2.4 onboarding redesign shipped June 28 introduced a UI regression on step 3 (connect data source). Error rate spiked to 38% on that step, causing 41% of new users to abandon setup entirely.',
    Viz: FunnelViz,
  },
  {
    id: 'f2', tag: 'CHANNEL', tagColor: '#1A56DB', severity: 'high',
    title: 'Direct Sales −34%',
    summary: 'Direct channel fell sharply from Jul 3 — one week after v2.4 shipped. SMB segment worst hit.',
    detail: 'Direct sales revenue dropped 34% from Jul 3 onward. This aligns with the v2.4 ship date (Jun 28) and a 5-day lag for trial-to-paid conversion.',
    Viz: ChannelViz,
  },
  {
    id: 'f3', tag: 'COHORT', tagColor: '#6B21A8', severity: 'high',
    title: 'July Cohort −28% LTV',
    summary: 'Users acquired in July 2024 show the lowest 6-month LTV on record. High churn before activation.',
    detail: 'The July 2024 acquisition cohort has a projected 6-month LTV 28% below the annual average. High early churn — within the first 7 days — is the primary driver.',
    Viz: CohortViz,
  },
  {
    id: 'f4', tag: 'RECOVERY', tagColor: '#065F46', severity: 'resolved',
    title: 'Retention Recovered Post-Hotfix',
    summary: 'Oct hotfix restored onboarding step 3. Retention climbed from 68% to 88% by December.',
    detail: 'After the October 12 hotfix that restored the onboarding step 3 flow, retention rates improved steadily. December reached 88% — surpassing the pre-regression baseline of 82%.',
    Viz: RetentionViz,
  },
  {
    id: 'f5', tag: 'SEGMENT', tagColor: '#B45309', severity: 'medium',
    title: 'SMB Self-Serve Most Exposed',
    summary: 'SMB customers relying on self-serve onboarding had 3× the churn rate of enterprise accounts.',
    detail: 'Enterprise accounts are onboarded by CSMs who bypassed the broken UI step entirely. SMB and mid-market customers using the self-serve flow were fully exposed.',
    Viz: SegmentViz,
  },
]

// ── Main component ─────────────────────────────────────────────

export default function VizPanel() {
  const [selected, setSelected] = useState(FINDINGS[0])
  const { Viz } = selected

  return (
    <div style={{ paddingTop: 64, height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* Stats strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, padding: '16px 28px 16px' }}>
        {[
          { label: 'Revenue Impact', value: '−$2.4M', sub: 'Q3 vs forecast', color: '#FF4500' },
          { label: 'Users Affected', value: '4,820', sub: 'Jul acquisitions', color: '#1A56DB' },
          { label: 'Time to Detect', value: '6 days', sub: 'Jun 28 → Jul 4', color: '#B45309' },
          { label: 'Status', value: 'Resolved', sub: 'Oct 12 hotfix', color: '#065F46' },
        ].map((s, i) => (
          <div key={i} className="clay-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: 'var(--gray)', marginBottom: 6 }}>{s.label}</div>
            <div style={{ fontSize: 26, fontWeight: 900, color: s.color, lineHeight: 1, fontFamily: 'var(--font-display)', marginBottom: 4 }}>{s.value}</div>
            <div style={{ fontSize: 11, color: 'var(--gray)', fontWeight: 600 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: 16, flex: 1, overflow: 'hidden', padding: '0 28px 24px' }}>
        {/* Left: finding list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, overflowY: 'auto', paddingRight: 4 }}>
          {FINDINGS.map((f) => {
            const sev = SEVERITY_STYLES[f.severity]
            const isActive = selected?.id === f.id
            return (
              <div key={f.id}
                onClick={() => setSelected(f)}
                className="clay-card"
                style={{
                  padding: '16px 18px', cursor: 'pointer',
                  borderLeft: `4px solid ${f.tagColor}`,
                  boxShadow: isActive
                    ? `0 8px 0 0 ${f.tagColor}55, 0 12px 28px ${f.tagColor}22, inset 0 1.5px 0 rgba(255,255,255,0.8)`
                    : undefined,
                  transform: isActive ? 'translateY(-2px)' : undefined,
                  transition: 'transform .15s, box-shadow .15s',
                }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: f.tagColor }}>{f.tag}</span>
                  <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', background: sev.bg, color: sev.color, padding: '2px 8px', borderRadius: 999 }}>{sev.label}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--black)', marginBottom: 6, lineHeight: 1.3 }}>{f.title}</div>
                <div style={{ fontSize: 12, color: 'var(--gray)', lineHeight: 1.5, fontWeight: 500 }}>{f.summary}</div>
                {isActive && (
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--line)', fontSize: 12, color: 'var(--black)', lineHeight: 1.6, fontWeight: 500 }}>
                    {f.detail}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Right: interactive viz */}
        <div className="clay-card" style={{ padding: '28px 32px', overflowY: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
            <div style={{ width: 12, height: 12, background: selected.tagColor, borderRadius: '50%', boxShadow: `0 4px 0 ${selected.tagColor}66` }} />
            <span style={{ fontSize: 11, fontWeight: 800, letterSpacing: '2px', textTransform: 'uppercase', color: selected.tagColor }}>{selected.tag}</span>
            <span style={{ fontSize: 16, fontWeight: 800, color: 'var(--black)', marginLeft: 4 }}>{selected.title}</span>
          </div>
          <Viz key={selected.id} />
        </div>
      </div>
    </div>
  )
}
