export type SourceType = 'file' | 'url' | 'readwise' | 'highlight' | 'obsidian'

export type NodeType = 'Document' | 'Highlight' | 'Cluster' | 'Tag'

export type EdgeType =
  | 'BELONGS_TO'
  | 'EXTRACTED_FROM'
  | 'SIMILAR_TO'
  | 'TAGGED'
  | 'CHILD_OF'

export interface KnowledgeNode {
  id: string
  title: string
  content?: string
  url?: string
  source: SourceType
  type: NodeType
  cluster?: string
  tags?: string[]
  createdAt?: string
  metadata?: Record<string, any>
  // For visualization
  x?: number
  y?: number
  z?: number
  color?: string
}

export interface KnowledgeEdge {
  source: string
  target: string
  type: EdgeType
  score?: number
}

export interface GraphData {
  nodes: KnowledgeNode[]
  links: KnowledgeEdge[]
}

export interface IngestRequest {
  source: SourceType | 'enerv'
  content: string
  title?: string
  url?: string
  cluster?: string
  tags?: string[]
  metadata?: Record<string, any>
}

export interface IngestResult {
  nodeId: string
  chunksCreated: number
  edgesCreated: number
  embedded: boolean
}
