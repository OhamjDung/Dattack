import { useState } from 'react'
import { Zap } from 'lucide-react'
import type { ContextRequest } from '../types/graph'

interface Props {
  onSubmit: (req: ContextRequest) => void
  loading: boolean
}

export default function ContextForm({ onSubmit, loading }: Props) {
  const [form, setForm] = useState<ContextRequest>({ goal: '', why: '', available_data: '', ideas: '' })

  function set(key: keyof ContextRequest) {
    return (e: React.ChangeEvent<HTMLTextAreaElement>) => setForm((f) => ({ ...f, [key]: e.target.value }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.goal.trim()) return
    onSubmit(form)
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-2 bg-indigo-600 text-white px-4 py-2 rounded-full mb-4">
            <Zap size={18} />
            <span className="font-bold text-lg tracking-tight">Dattack</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-800 mb-2">What would you like to discover?</h1>
          <p className="text-slate-500">Tell us about your data and goal — we'll build a live analysis map.</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 space-y-5">
          <Field label="Goal" placeholder="e.g. Understand why revenue dropped in Q3" value={form.goal} onChange={set('goal')} required />
          <Field label="Why this matters" placeholder="e.g. Board presentation next week, need actionable insights" value={form.why} onChange={set('why')} />
          <Field label="Available datasets" placeholder="e.g. Sales CSV (Jan–Dec 2024), Customer DB export, marketing spend sheet" value={form.available_data} onChange={set('available_data')} />
          <Field label="Ideas or techniques" placeholder="e.g. Cohort analysis, churn prediction, seasonality check" value={form.ideas} onChange={set('ideas')} />

          <button
            type="submit"
            disabled={loading || !form.goal.trim()}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
          >
            {loading ? 'Building your map…' : 'Start Research →'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Field({ label, placeholder, value, onChange, required }: {
  label: string
  placeholder: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void
  required?: boolean
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-slate-700 mb-1">
        {label}{required && <span className="text-indigo-500 ml-1">*</span>}
      </label>
      <textarea
        className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
        rows={3}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        required={required}
      />
    </div>
  )
}
