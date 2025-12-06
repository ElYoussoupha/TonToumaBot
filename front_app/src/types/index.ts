export interface Entity {
  entity_id: string;
  name: string;
  description?: string;
  contact_email?: string;
  created_at: string;
  updated_at: string;
}

export interface Instance {
  instance_id: string;
  entity_id: string;
  name: string;
  location?: string;
  status: 'active' | 'inactive' | 'maintenance';
  created_at: string;
  last_heartbeat?: string;
}

export interface Session {
  session_id: string;
  entity_id: string;
  speaker_id?: string;
  start_time: string;
  end_time?: string;
  is_active: boolean;
}

export interface Message {
  message_id: string;
  session_id: string;
  instance_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  audio_path?: string;
  created_at: string;
}

export interface Speaker {
  speaker_id: string;
  name?: string;
  first_seen: string;
}

export interface KnowledgeChunk {
  chunk_id: string;
  doc_id: string;
  chunk_index: number;
  content: string;
  created_at: string;
}

export interface KBDocument {
  doc_id: string;
  entity_id: string;
  title: string;
  source?: string;
  created_at: string;
  chunks: KnowledgeChunk[];
}
