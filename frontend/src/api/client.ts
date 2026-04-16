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

export async function submitContext(
  req: ContextRequest,
  file: File | null,
): Promise<{ nodes: DattackNode[]; edges: DattackEdge[]; pending_session_id?: string }> {
  const form = new FormData()
  form.append('goal', req.goal)
  form.append('why', req.why)
  form.append('available_data', req.available_data)
  form.append('ideas', req.ideas)
  if (file) form.append('file', file)

  const res = await fetch(`${BASE}/context`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`/context failed: ${res.status}`)
  return res.json()
}

export async function runResearch(
  sessionId: string,
  nodes: DattackNode[],
): Promise<{ new_nodes: DattackNode[]; new_edges: DattackEdge[] }> {
  return post('/research', { session_id: sessionId, nodes })
}

export async function submitFeedback(
  nodeId: string,
  feedback: string,
  deeperResearch: boolean,
  nodes: DattackNode[],
): Promise<{ updated_nodes: DattackNode[]; new_edges: DattackEdge[] }> {
  return post('/feedback', { node_id: nodeId, feedback, deeper_research: deeperResearch, nodes })
}

export async function approveMap(
  nodes: DattackNode[],
  edges: DattackEdge[],
  pendingSessionId?: string,
): Promise<{ session_id: string; status: string }> {
  return post('/approve', { nodes, edges, pending_session_id: pendingSessionId })
}

export function createSSEStream(
  sessionId: string,
  onLog: (msg: string) => void,
  onNodeAdd: (node: DattackNode, edge: DattackEdge) => void,
  onComplete: (summary: string) => void,
): EventSource {
  const es = new EventSource(`${BASE}/stream?session_id=${sessionId}`)

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
