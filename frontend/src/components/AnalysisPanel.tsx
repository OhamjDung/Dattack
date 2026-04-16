import { useEffect, useRef } from 'react'
import { Activity } from 'lucide-react'
import { createSSEStream } from '../api/client'
import type { DattackNode, DattackEdge } from '../types/graph'

interface Props {
  sessionId: string
  log: string[]
  onLog: (msg: string) => void
  onNodeAdd: (node: DattackNode, edge: DattackEdge) => void
  onComplete: (summary: string) => void
}

export default function AnalysisPanel({ sessionId, log, onLog, onNodeAdd, onComplete }: Props) {
  const logRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = createSSEStream(sessionId, onLog, onNodeAdd, onComplete)
    esRef.current = es
    return () => {
      es.close()
      esRef.current = null
    }
  }, [sessionId])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  return (
    <div className="fixed bottom-0 left-0 right-0 h-56 bg-slate-900 border-t border-slate-700 flex flex-col">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-slate-700">
        <Activity size={14} className="text-indigo-400 animate-pulse" />
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wide">Live Analysis</span>
        <span className="text-xs text-slate-500 ml-1">Session {sessionId.slice(0, 8)}</span>
      </div>
      <div ref={logRef} className="flex-1 overflow-auto px-4 py-2 space-y-1 font-mono">
        {log.map((line, i) => (
          <div key={i} className="text-xs text-slate-300">
            <span className="text-indigo-400 mr-2">›</span>{line}
          </div>
        ))}
        {log.length === 0 && (
          <div className="text-xs text-slate-500 italic">Initializing analysis stream…</div>
        )}
        <div className="inline-block w-1.5 h-3 bg-indigo-400 animate-pulse ml-4" />
      </div>
    </div>
  )
}
