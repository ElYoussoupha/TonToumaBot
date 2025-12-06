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

export interface Specialty {
  specialty_id: string;
  name: string;
  description?: string;
  created_at: string;
}

export interface Doctor {
  doctor_id: string;
  entity_id: string;
  specialty_id?: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  consultation_duration: number;
  is_active: boolean;
  created_at: string;
  specialty_name?: string;
}

export interface DoctorCredentials {
  doctor_id: string;
  email: string;
  temporary_password: string;
  message: string;
}

export interface TimeSlot {
  slot_id: string;
  doctor_id: string;
  day_of_week?: number;
  specific_date?: string;
  start_time: string;
  end_time: string;
  is_recurring: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Appointment {
  appointment_id: string;
  doctor_id: string;
  session_id?: string;
  patient_name: string;
  patient_email: string;
  patient_phone?: string;
  reason: string;
  date: string;
  start_time: string;
  end_time: string;
  status: 'pending' | 'confirmed' | 'cancelled' | 'completed';
  created_at: string;
  doctor_first_name?: string;
  doctor_last_name?: string;
  specialty_name?: string;
}
