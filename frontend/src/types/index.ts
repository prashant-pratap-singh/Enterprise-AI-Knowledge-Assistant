// Enterprise AI Knowledge Assistant - Shared TypeScript Types

export type UserRole = 'ADMIN' | 'EDITOR' | 'VIEWER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  created_at: string;
}

export interface Workspace {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export type DocumentStatus = 'uploaded' | 'processing' | 'indexed' | 'failed' | 'deleting';

export interface Document {
  id: string;
  organization_id: string;
  workspace_id: string;
  uploaded_by: string;
  filename: string;
  file_type: string;
  file_size: number;
  checksum: string;
  status: DocumentStatus;
  page_count: number | null;
  chunk_count: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  citation_id: number;
  document_id: string;
  filename: string;
  page_number?: number | null;
  chunk_id: string;
  excerpt: string;
  similarity_score?: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  citations?: Citation[];
  retrieval_metadata?: Record<string, unknown>;
  created_at: string;
}

export interface Conversation {
  id: string;
  workspace_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages?: Message[];
}

export interface EvaluationRun {
  id: string;
  organization_id: string;
  dataset_name: string;
  metrics: {
    faithfulness?: number;
    answer_relevance?: number;
    context_precision?: number;
    context_recall?: number;
    citation_correctness?: number;
    avg_latency_ms?: number;
    total_tokens?: number;
  };
  configuration: Record<string, unknown>;
  created_at: string;
}
