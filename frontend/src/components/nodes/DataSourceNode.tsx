import { Handle, Position } from 'reactflow'
import { Database } from 'lucide-react'
import type { NodeData } from '../../types/graph'

export default function DataSourceNode({ data }: { data: NodeData }) {
  const rows = data.metadata?.rows as number | undefined
  const source = data.metadata?.source as string | undefined

  return (
    <div className="bg-blue-50 border-2 border-blue-300 rounded-xl px-4 py-3 w-48 shadow">
      <Handle type="source" position={Position.Right} className="opacity-0" />
      <div className="flex items-center gap-2 mb-1">
        <Database size={14} className="text-blue-500 shrink-0" />
        <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">Data Source</span>
      </div>
      <div className="font-semibold text-sm text-slate-800 leading-snug">{data.label}</div>
      <div className="text-xs text-slate-500 mt-1 leading-snug">{data.description}</div>
      {rows && (
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">{rows.toLocaleString()} rows</span>
          {source && <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{source}</span>}
        </div>
      )}
    </div>
  )
}
