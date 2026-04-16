import React, { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  ReactFlowProvider,
} from 'reactflow'
import 'reactflow/dist/style.css'
import type { Connection } from 'reactflow'
import { CheckCircle, MessageSquare } from 'lucide-react'

import GoalNode from './nodes/GoalNode'
import DataSourceNode from './nodes/DataSourceNode'
import TechniqueNode from './nodes/TechniqueNode'
import QuestionNode from './nodes/QuestionNode'
import FindingNode from './nodes/FindingNode'
import type { DattackNode, DattackEdge } from '../types/graph'
import { submitFeedback } from '../api/client'

const nodeTypes: Record<string, React.ComponentType<any>> = {
  goalNode: GoalNode,
  dataSourceNode: DataSourceNode,
  techniqueNode: TechniqueNode,
  questionNode: QuestionNode,
  findingNode: FindingNode,
}

interface Props {
  initialNodes: DattackNode[]
  initialEdges: DattackEdge[]
  onApprove: (nodes: DattackNode[], edges: DattackEdge[]) => void
  externalNodes?: DattackNode[]
  externalEdges?: DattackEdge[]
}

function MapCanvas({ initialNodes, initialEdges, onApprove, externalNodes = [], externalEdges = [] }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes as any)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges as any)
  const containerRef = React.useRef<HTMLDivElement>(null)
  const [selected, setSelected] = useState<DattackNode | null>(null)
  const [popupPos, setPopupPos] = useState({ x: 0, y: 0 })
  const [feedback, setFeedback] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges])

  useEffect(() => {
    if (!externalNodes.length) return
    setNodes((ns) => {
      const existingIds = new Set(ns.map((n) => n.id))
      const incoming = externalNodes.filter((n) => !existingIds.has(n.id))
      return incoming.length ? [...ns, ...incoming as any] : ns
    })
  }, [externalNodes])

  useEffect(() => {
    if (!externalEdges.length) return
    setEdges((es) => {
      const existingIds = new Set(es.map((e) => e.id))
      const incoming = externalEdges.filter((e) => !existingIds.has(e.id))
      return incoming.length ? [...es, ...incoming as any] : es
    })
  }, [externalEdges])

  const hasOpenQuestions = nodes.some((n: any) => n.data.type === 'question' && n.data.status !== 'answered')

  function handleNodeClick(e: React.MouseEvent, node: any) {
    const rect = containerRef.current?.getBoundingClientRect()
    setPopupPos({
      x: e.clientX - (rect?.left ?? 0),
      y: e.clientY - (rect?.top ?? 0),
    })
    setSelected(node as DattackNode)
    setFeedback('')
  }

  async function handleFeedbackSubmit(deeper: boolean) {
    if (!selected || !feedback.trim()) return
    setSubmitting(true)
    try {
      const res = await submitFeedback(selected.id, feedback, deeper, nodes as any)
      setNodes((ns) => {
        const updatedIds = new Set(res.updated_nodes.map((n) => n.id))
        const merged = ns.map((n) => {
          const upd = res.updated_nodes.find((u) => u.id === n.id)
          return upd ? { ...n, ...upd } : n
        })
        const brand_new = res.updated_nodes.filter((n) => !updatedIds.has(n.id) && !ns.find((e) => e.id === n.id))
        return [...merged, ...brand_new] as any
      })
      setEdges((es) => [...es, ...res.new_edges] as any)
      setSelected(null)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div ref={containerRef} className="w-full h-screen relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        nodeTypes={nodeTypes}
        fitView
        className="bg-slate-100"
      >
        <Background color="#cbd5e1" gap={20} />
        <Controls />
        <MiniMap nodeColor={(n) => {
          const t = (n.data as any)?.type
          if (t === 'goal') return '#4f46e5'
          if (t === 'data_source') return '#3b82f6'
          if (t === 'technique') return '#a855f7'
          if (t === 'question') return '#f59e0b'
          if (t === 'finding') return '#10b981'
          return '#94a3b8'
        }} />
      </ReactFlow>

      <button
        disabled={hasOpenQuestions}
        onClick={() => onApprove(nodes as any, edges as any)}
        className="absolute bottom-6 right-6 flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold px-5 py-3 rounded-xl shadow-lg transition-colors"
      >
        <CheckCircle size={18} />
        {hasOpenQuestions ? 'Answer all questions to approve' : 'Approve Map'}
      </button>

      {selected && (
        <div
          className="absolute z-50 w-64 bg-white rounded-xl shadow-2xl border border-slate-200 p-3"
          style={{
            left: Math.min(popupPos.x + 12, window.innerWidth - 280),
            top: Math.min(popupPos.y + 12, window.innerHeight - 240),
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5">
              <MessageSquare size={13} className="text-indigo-500" />
              <span className="text-xs font-semibold text-slate-700">{selected.data.label}</span>
            </div>
            <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600 text-base leading-none">×</button>
          </div>
          <textarea
            autoFocus
            className="w-full border border-slate-200 rounded-lg px-2.5 py-2 text-xs text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
            rows={3}
            placeholder="Tell the AI what to change or explore…"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFeedbackSubmit(false) } }}
          />
          <div className="flex gap-1.5 mt-2">
            <button
              disabled={!feedback.trim() || submitting}
              onClick={() => handleFeedbackSubmit(false)}
              className="flex-1 bg-slate-700 hover:bg-slate-800 disabled:opacity-40 text-white text-xs font-medium py-1.5 rounded-lg transition-colors"
            >
              Update
            </button>
            <button
              disabled={!feedback.trim() || submitting}
              onClick={() => handleFeedbackSubmit(true)}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white text-xs font-medium py-1.5 rounded-lg transition-colors"
            >
              Deep Research
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function MapView(props: Props) {
  return (
    <ReactFlowProvider>
      <MapCanvas {...props} />
    </ReactFlowProvider>
  )
}
