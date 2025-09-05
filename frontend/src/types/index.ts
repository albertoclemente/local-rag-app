export interface Document {
  id: string
  filename: string
  title?: string
  size: number
  upload_date: string
  file_type: string
  chunk_count?: number
  indexed: boolean
  tags: string[]
  metadata: Record<string, any>
}

export interface DocumentUploadRequest {
  file: File
  title?: string
  tags?: string[]
}

export interface DocumentUpdateRequest {
  title?: string
  tags?: string[]
}

export interface ChunkResult {
  content: string
  score: number
  metadata: {
    doc_id: string
    chunk_index: number
    page_number?: number
  }
}

export interface Citation {
  chunk_index: number
  doc_id: string
  doc_title: string
  page_number?: number
  relevance_score: number
  content_preview: string
}

export interface QueryRequest {
  query: string
  k?: number
  doc_filter?: string[]
  min_score?: number
}

export interface QueryResponse {
  answer: string
  chunks: ChunkResult[]
  citations: Citation[]
  complexity: 'simple' | 'moderate' | 'complex'
  query_id: string
  processing_time: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  citations?: Citation[]
  query_id?: string
}

export interface SystemStatus {
  status: 'operational' | 'degraded' | 'offline' | 'error'
  cpu_usage?: number
  ram_usage?: number
  indexing_progress?: number
  offline: boolean
}

export interface Settings {
  rag_profile: 'eco' | 'balanced' | 'performance'
  chunk_size: number
  chunk_overlap: number
  retrieval_k: number
  min_relevance_score: number
  llm_temperature: number
  max_tokens: number
  system_prompt?: string
}

export type RAGProfile = typeof import('../lib/constants').RAG_PROFILES[keyof typeof import('../lib/constants').RAG_PROFILES]
export type QueryComplexity = typeof import('../lib/constants').QUERY_COMPLEXITY[keyof typeof import('../lib/constants').QUERY_COMPLEXITY]
