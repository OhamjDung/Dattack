import { Handle, Position } from 'reactflow'
import { HelpCircle } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function QuestionNode({ data }: { id: string; data: NodeData }) {
  return (
    <div className="rounded-xl px-4 py-3 w-56 shadow border-2 bg-amber-50 border-amber-300">
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <HelpCircle size={14} className="text-amber-500" />
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-600">Question</span>
      </div>
      <div className="font-semibold text-sm text-slate-800 leading-snug">{data.label}</div>
      <div className="text-xs text-slate-500 mt-1 leading-snug">{data.description}</div>
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
