import { useState } from 'react'
import { Handle, Position, useReactFlow } from 'reactflow'
import { HelpCircle } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function QuestionNode({ id, data }: { id: string; data: NodeData }) {
  const [answer, setAnswer] = useState('')
  const { setNodes } = useReactFlow()

  const answered = data.status === 'answered'

  function handleAnswer() {
    if (!answer.trim()) return
    setNodes((nodes) =>
      nodes.map((n) =>
        n.id === id
          ? { ...n, data: { ...n.data, status: 'answered', metadata: { ...n.data.metadata, answer } } }
          : n
      )
    )
  }

  return (
    <div className={`rounded-xl px-4 py-3 w-56 shadow border-2 transition-colors ${answered ? 'bg-green-50 border-green-300' : 'bg-amber-50 border-amber-300'}`}>
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <HelpCircle size={14} className={answered ? 'text-green-500' : 'text-amber-500'} />
        <span className={`text-xs font-semibold uppercase tracking-wide ${answered ? 'text-green-600' : 'text-amber-600'}`}>
          {answered ? 'Answered' : 'Question'}
        </span>
      </div>
      <div className="font-semibold text-sm text-slate-800 leading-snug">{data.label}</div>
      <div className="text-xs text-slate-500 mt-1 leading-snug">{data.description}</div>
      {!answered && (
        <div className="mt-2 flex gap-1">
          <input
            className="flex-1 text-xs border border-amber-300 rounded px-2 py-1 focus:outline-none focus:border-amber-500 bg-white"
            placeholder="Your answer…"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAnswer()}
          />
          <button
            className="text-xs bg-amber-400 hover:bg-amber-500 text-white px-2 py-1 rounded transition-colors"
            onClick={handleAnswer}
          >
            OK
          </button>
        </div>
      )}
      {answered && (
        <div className="mt-2 text-xs text-green-700 bg-green-100 rounded px-2 py-1">
          {String((data.metadata as Record<string, unknown>)?.answer ?? '')}
        </div>
      )}
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
