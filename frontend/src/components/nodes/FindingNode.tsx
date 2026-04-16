import { Handle, Position } from 'reactflow'
import { TrendingUp } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function FindingNode({ data }: { data: NodeData }) {
  const correlation = data.metadata?.correlation as number | undefined

  return (
    <div className="bg-emerald-50 border-2 border-emerald-300 rounded-xl px-4 py-3 w-52 shadow animate-in fade-in">
      <Handle type="target" position={Position.Left} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <TrendingUp size={14} className="text-emerald-500 shrink-0" />
        <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wide">Finding</span>
      </div>
      <div className="font-semibold text-sm text-slate-800 leading-snug">{data.label}</div>
      <div className="text-xs text-slate-500 mt-1 leading-snug">{data.description}</div>
      {correlation !== undefined && (
        <div className="mt-2 text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full w-fit">
          r = {correlation.toFixed(2)}
        </div>
      )}
    </div>
  )
}
