import { Handle, Position } from 'reactflow'
import { Star } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function GoalNode({ data }: { data: NodeData }) {
  return (
    <div className="bg-indigo-600 text-white rounded-2xl px-5 py-4 w-56 shadow-lg border-2 border-indigo-700">
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <Star size={16} className="shrink-0" />
        <span className="text-xs font-semibold uppercase tracking-wide opacity-80">Goal</span>
      </div>
      <div className="font-bold text-sm leading-snug">{data.label}</div>
      <div className="text-xs mt-1 opacity-70 leading-snug">{data.description}</div>
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
