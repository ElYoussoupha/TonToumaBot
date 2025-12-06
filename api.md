# API Reference

Base URL: `http://localhost:9000/api/v1`

Auth: aucune (développement). Les CORS sont ouverts.

## Conventions
- IDs: UUIDv4
- Dates: ISO 8601
- DTOs: voir sections Response/Request ci-dessous

---

## Entities

- POST `/entities`
  - Request (JSON): `{ name: string, description?: string, contact_email?: string }`
  - Response: `EntityResponse`
- GET `/entities`
  - Query: `skip?`, `limit?`
  - Response: `EntityResponse[]`
- GET `/entities/{entity_id}`
  - Response: `EntityResponse`
- PUT `/entities/{entity_id}`
  - Request (JSON): `{ name?: string, description?: string, contact_email?: string }`
  - Response: `EntityResponse`
- DELETE `/entities/{entity_id}`
  - Response: `EntityResponse`

DTO: `EntityResponse`
```
{
  entity_id: string,
  name: string,
  description?: string,
  contact_email?: string,
  created_at: string,
  updated_at: string
}
```

### Instances
- POST `/instances`
  - Request (JSON): `{ entity_id: string, name: string, location?: string, status: 'active'|'inactive'|'maintenance' }`
  - Response: `InstanceResponse` (inclut un `api_key` généré côté serveur)
- GET `/instances`
  - Response: `InstanceResponse[]`
- GET `/instances/{instance_id}`
  - Response: `InstanceResponse`
- PUT `/instances/{instance_id}`
  - Request (JSON): `{ name?: string, location?: string, status?: ... }`
  - Response: `InstanceResponse`
- DELETE `/instances/{instance_id}`
  - Response: `InstanceResponse`

DTO: `InstanceResponse`
```
{
  instance_id: string,
  entity_id: string,
  name: string,
  location?: string,
  status: 'active'|'inactive'|'maintenance',
  created_at: string,
  last_heartbeat?: string,
  api_key?: string
}
```

---

## Sessions & Messages

- POST `/sessions`
  - Request (JSON): `{ entity_id: string, speaker_id?: string, is_active?: boolean }`
  - Response: `SessionResponse`
- GET `/sessions`
  - Response: `SessionResponse[]`
- GET `/sessions/{session_id}`
  - Response: `SessionResponse`
- GET `/sessions/{session_id}/messages`
  - Response: `MessageResponse[]`

DTOs:
```
SessionResponse {
  session_id: string,
  entity_id: string,
  speaker_id?: string,
  created_at: string,
  expires_at?: string,
  is_active: boolean
}

MessageResponse {
  message_id: string,
  session_id: string,
  instance_id: string,
  role: 'user'|'assistant'|'system',
  content?: string,
  audio_path?: string,
  tokens?: number,
  created_at: string
}
```

---

## Chat

### 1) Message vocal
- POST `/chat/messages` (multipart/form-data)
  - Form fields:
    - `instance_id`: string (UUID)
    - `audio_file`: file (wav recommandé)
    - `speaker_id?`: ignoré (speaker fixe en démo)
    - `metadata?`: string
  - Response (JSON):
```
{
  speaker_id: string,
  session_id: string,
  transcription: string,
  user_audio: string,           // chemin relatif ex: uploads/xxx.wav
  response_text: string,
  response_audio: string        // chemin relatif ex: uploads/xxx.mp3
}
```

### 2) Message texte
- POST `/chat/text` (application/json)
  - Body: `{ instance_id: string, text: string }`
  - Response: identique au vocal, avec `user_audio: null` et `transcription = text`.

Notes:
- Le `speaker_id` est fixe en mode démo: `11111111-1111-1111-1111-111111111111`.
- Les fichiers audio sont servis via `GET http://localhost:9000/uploads/...`.

---

## Knowledge Base (KB)

### Lire les documents
- GET `/kb/documents/{entity_id}`
  - Response: `KBDocumentResponse[]` (avec `chunks`)

### Créer via upload de fichier
- POST `/kb/documents` (multipart/form-data)
  - Form: `title`, `file`, `entity_id`
  - Le fichier est stocké (MinIO) et un texte est extrait (PDF supporté basique, sinon UTF-8), puis découpé en chunks et vectorisé.
  - Response: `KBDocumentResponse` (avec `chunks`)

### Upload simple (legacy)
- POST `/kb/upload` (multipart/form-data)
  - Form: `entity_id`, `file`
  - Décodage texte simple et création d’un document.

### Créer depuis un texte brut
- POST `/kb/text` (multipart/form-data)
  - Form: `title`, `content`, `entity_id`
  - Découpe en chunks de 500 chars + embeddings.
  - Response: `KBDocumentResponse` (avec `chunks`)

### Lire les chunks d’un document
- GET `/kb/chunks/{doc_id}`
  - Response: `KBChunkResponse[]`

### Embeddings
- POST `/kb/embeddings`
  - Body (JSON): `{ chunk_id: string, embedding: number[] }`
  - Response: `KBEmbeddingResponse`
- GET `/kb/embeddings/{chunk_id}`
  - Response: `KBEmbeddingResponse`

### Supprimer un document
- DELETE `/kb/documents/{doc_id}`
  - Response: `KBDocumentResponse`

DTOs:
```
KBDocumentResponse {
  doc_id: string,
  entity_id: string,
  title: string,
  source?: string,
  created_at: string,
  chunks: KBChunkResponse[]
}

KBChunkResponse {
  chunk_id: string,
  doc_id: string,
  chunk_index: number,
  content: string,
  created_at: string
}

KBEmbeddingResponse {
  chunk_id: string,
  embedding: number[]
}
```

---

## Exemples cURL

Créer une entité:
```
curl -X POST http://localhost:9000/api/v1/entities \
  -H "Content-Type: application/json" \
  -d '{"name":"Hopital Fann","description":"Chatbot accueil"}'
```

Uploader un fichier KB:
```
curl -X POST http://localhost:9000/api/v1/kb/documents \
  -F title="Guide accueil" \
  -F entity_id="<ENTITY_ID>" \
  -F file=@/path/to/file.pdf
```

Créer un doc KB depuis du texte:
```
curl -X POST http://localhost:9000/api/v1/kb/text \
  -F title="Consignes" \
  -F content="Voici des informations utiles..." \
  -F entity_id="<ENTITY_ID>"
```

Tester le chat texte:
```
curl -X POST http://localhost:9000/api/v1/chat/text \
  -H "Content-Type: application/json" \
  -d '{"instance_id":"<INSTANCE_ID>", "text":"Bonjour"}'
```

Tester le chat audio:
```
curl -X POST http://localhost:9000/api/v1/chat/messages \
  -F instance_id="<INSTANCE_ID>" \
  -F audio_file=@/path/to/audio.wav
```
