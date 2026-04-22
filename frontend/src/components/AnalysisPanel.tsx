import { useEffect, useRef } from 'react'
import { createSSEStream } from '../api/client'
import type { DattackNode, DattackEdge } from '../types/graph'

interface Props {
  sessionId: string
  log: string[]
  onLog: (msg: string) => void
  onNodeAdd: (node: DattackNode, edge: DattackEdge) => void
  onComplete: (summary: string) => void
  isComplete?: boolean
}

export default function AnalysisPanel({ sessionId, log, onLog, onNodeAdd, onComplete, isComplete = false }: Props) {
  const logRef = useRef<HTMLDivElement>(null)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    if (!sessionId) return
    esRef.current = createSSEStream(sessionId, onLog, onNodeAdd, onComplete)
    return () => { esRef.current?.close() }
  }, [sessionId])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight
  }, [log])

  return (
    <div className="terminal-panel">
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '14px 20px',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        {!isComplete && <div className="pulse-dot" />}
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 10, fontWeight: 700, letterSpacing: '3px', textTransform: 'uppercase', color: 'var(--orange)' }}>
          Live Analysis
        </div>
        <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)', marginLeft: 8, fontFamily: 'monospace' }}>
          {sessionId.slice(0, 8)}
        </span>
      </div>

      <div ref={logRef} className="terminal-log">
        {log.length === 0 && (
          <div className="log-line" style={{ color: 'rgba(255,255,255,0.3)', fontStyle: 'italic' }}>Initializing…</div>
        )}
        {log.map((line, i) => (
          <div key={i} className={`log-line${line.startsWith('✓') ? ' done-line' : ''}`}>
            <span className="prompt">{line.startsWith('✓') ? '✓' : '›'}</span>
            {line.replace(/^✓\s?/, '')}
          </div>
        ))}
        {!isComplete && (
          <div className="log-line">
            <span className="prompt">›</span>
            <span className="cursor-blink" />
          </div>
        )}
      </div>
    </div>
  )
}
