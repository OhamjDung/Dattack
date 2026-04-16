import { Handle, Position } from 'reactflow'
import { Layers } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function TechniqueNode({ data }: { data: NodeData }) {
  return (
    <div className="bg-purple-50 border-2 border-purple-300 rounded-xl px-4 py-3 w-48 shadow">
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <Layers size={14} className="text-purple-500 shrink-0" />
        <span className="text-xs font-semibold text-purple-600 uppercase tracking-wide">Technique</span>
      </div>
      <div className="font-semibold text-sm text-slate-800 leading-snug">{data.label}</div>
      <div className="text-xs text-slate-500 mt-1 leading-snug">{data.description}</div>
      <Handle type="source" position={Position.Right} className="opacity-0" />
    </div>
  )
}
