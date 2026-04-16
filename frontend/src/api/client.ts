import type { ContextRequest, DattackNode, DattackEdge } from '../types/graph'

const BASE = 'http://localhost:8000'

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`)
  return res.json()
}

export async function submitContext(req: ContextRequest): Promise<{ nodes: DattackNode[]; edges: DattackEdge[] }> {
  return post('/context', req)
}

export async function runResearch(sessionId: string): Promise<{ new_nodes: DattackNode[]; new_edges: DattackEdge[] }> {
  return post('/research', { session_id: sessionId })
}

export async function submitFeedback(
  nodeId: string,
  feedback: string,
  deeperResearch = false
): Promise<{ updated_nodes: DattackNode[]; new_edges: DattackEdge[] }> {
  return post('/feedback', { node_id: nodeId, feedback, deeper_research: deeperResearch })
}

export async function approveMap(
  nodes: DattackNode[],
  edges: DattackEdge[]
): Promise<{ session_id: string; status: string }> {
  return post('/approve', { nodes, edges })
}

export function createSSEStream(onLog: (msg: string) => void, onNodeAdd: (node: DattackNode, edge: DattackEdge) => void, onComplete: (summary: string) => void): EventSource {
  const es = new EventSource(`${BASE}/stream`)

  es.addEventListener('log', (e) => {
    const data = JSON.parse(e.data)
    onLog(data.message)
  })

  es.addEventListener('node_add', (e) => {
    const data = JSON.parse(e.data)
    onNodeAdd(data.node, data.edge)
  })

  es.addEventListener('complete', (e) => {
    const data = JSON.parse(e.data)
    onComplete(data.summary)
    es.close()
  })

  return es
}
