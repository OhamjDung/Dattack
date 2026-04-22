import { useState } from 'react'
import type { ContextRequest } from '../types/graph'

interface Props {
  onSubmit: (req: ContextRequest, file: File | null) => void
  loading: boolean
}

export default function ContextForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<ContextRequest>({ goal: '', why: '', available_data: '', ideas: '' })
  const [file, setFile] = useState<File | null>(null)
  const set = (k: keyof ContextRequest) => (e: React.ChangeEvent<HTMLTextAreaElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }))

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.goal.trim()) return
    onSubmit(form, file)
  }

  return (
    <div style={{ paddingTop: 64, minHeight: '100vh' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0 }}>
        <div style={{ padding: '32px 36px', borderRight: '1px solid var(--line)' }}>
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <div className="form-field">
              <label>Analysis Goal <span>*</span></label>
              <textarea rows={3} value={form.goal} onChange={set('goal')} required
                placeholder="e.g. Understand why revenue dropped in Q3" />
            </div>
            <div className="form-field">
              <label>Why this matters</label>
              <textarea rows={2} value={form.why} onChange={set('why')}
                placeholder="e.g. Board presentation next week" />
            </div>
            <div className="form-field">
              <label>Upload Dataset <span style={{ color: 'var(--gray2)', fontWeight: 400 }}>(CSV / TSV)</span></label>
              <label className={`file-zone${file ? ' has-file' : ''}`}>
                <input type="file" accept=".csv,.tsv" style={{ display: 'none' }}
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M8 1v10M4 5l4-4 4 4M2 13h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
                {file
                  ? <span style={{ fontWeight: 600 }}>{file.name} — {(file.size / 1024).toFixed(0)} KB</span>
                  : <span>Click to upload</span>}
              </label>
            </div>
            <div className="form-field">
              <label>Describe your data</label>
              <textarea rows={2} value={form.available_data} onChange={set('available_data')}
                placeholder="e.g. Sales CSV, Jan–Dec 2024" />
            </div>
            <div className="form-field">
              <label>Ideas or techniques</label>
              <textarea rows={2} value={form.ideas} onChange={set('ideas')}
                placeholder="e.g. Cohort analysis, churn regression" />
            </div>
            <button type="submit" className="btn-primary" disabled={loading || !form.goal.trim()}>
              {loading ? 'Building map…' : <>Start Research <span style={{ marginLeft: 4 }}>→</span></>}
            </button>
          </form>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', padding: '32px 24px', gap: 16 }}>
          {[
            { step: '01', label: 'Define', desc: 'Describe your goal and upload your dataset. The more context, the sharper the map.' },
            { step: '02', label: 'Map', desc: 'Review an AI-generated analysis graph of data sources, techniques, and open questions.' },
            { step: '03', label: 'Refine', desc: 'Click nodes to give feedback, run deep research, and answer every question node.' },
            { step: '04', label: 'Discover', desc: 'Approve the map and watch a live analysis stream populate new findings in real time.' },
          ].map((item) => (
            <div key={item.step} style={{
              padding: '20px 24px', borderRadius: 'var(--radius-sm)',
              background: 'var(--white)', boxShadow: 'var(--shadow-card)',
              display: 'flex', gap: 20, alignItems: 'flex-start',
            }}>
              <div style={{ fontFamily: 'var(--font-display)', fontSize: 11, fontWeight: 900, color: 'var(--orange)', minWidth: 28 }}>
                {item.step}
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '1px', textTransform: 'uppercase', marginBottom: 6 }}>
                  {item.label}
                </div>
                <div style={{ fontSize: 13, color: 'var(--gray)', lineHeight: 1.6 }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
