export type NodeType = 'goal' | 'data_source' | 'technique' | 'question' | 'finding' | 'insight'
export type NodeStatus = 'pending' | 'active' | 'answered' | 'complete'

export interface NodeData {
  label: string
  description: string
  type: NodeType
  status?: NodeStatus
  metadata?: Record<string, unknown>
}

export interface NodePosition {
  x: number
  y: number
}

export interface DattackNode {
  id: string
  type: string
  position: NodePosition
  data: NodeData
}

export interface DattackEdge {
  id: string
  source: string
  target: string
  animated?: boolean
}

export interface ContextRequest {
  goal: string
  why: string
  available_data: string
  ideas: string
}

export interface StreamLogEvent {
  message: string
}

export interface StreamNodeAddEvent {
  node: DattackNode
  edge: DattackEdge
}

export interface StreamCompleteEvent {
  summary: string
}
