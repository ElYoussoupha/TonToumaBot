# Tontouma Voice Chatbot

Assistant vocal et texte pour entités (ex. hôpital), avec RAG (base de connaissances) et génération de réponses, servi par un backend FastAPI et un frontend Next.js.

## Stack
- Backend: FastAPI, SQLAlchemy (Async), PostgreSQL, pgvector, Alembic
- ASR/TTS: faster-whisper (ASR), gTTS (TTS)
- RAG: sentence-transformers (all-MiniLM-L6-v2)
- Stockage: MinIO (pour les fichiers de connaissance uploadés), dossier local `uploads/` pour audios
- Frontend: Next.js + TypeScript + Tailwind + Radix UI

## Structure
- `app/` Backend FastAPI
  - `api/v1/` routes (entities, users, sessions, kb, chat)
  - `models/` modèles SQLAlchemy (entities, chat, knowledge, ...)
  - `services/` audio, rag, llm, storage
  - `core/` config, database
- `front_app/` Front Next.js
- `migrations/` Alembic

## Prérequis
- Python 3.10+
- Node 18+
- PostgreSQL 15+ avec extension `pgvector`
- (Optionnel pour upload doc) MinIO

## Configuration
Créez un fichier `.env` à la racine (exemple minimal):
```
# Base de données
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=tontouma
POSTGRES_PORT=5432

# Clé API Gemini (si LLM Google)
GEMINI_API_KEY=

# Dossier uploads
UPLOAD_DIR=uploads

# MinIO (pour KB upload)
MINIO_ENDPOINT=localhost:9100
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=tontouma-knowledge
MINIO_SECURE=false
```

Frontend: créez/ajustez `front_app/.env.local` (ou variable env shell):
```
NEXT_PUBLIC_API_URL=http://localhost:9000/api/v1
```

## Installation & Lancement
1) Backend (FastAPI):
- Créez l’environnement Python et installez:
```
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```
- Initialisez la base (créez la DB `tontouma`, installez l’extension pgvector):
```
-- Dans psql (exemple):
CREATE DATABASE tontouma;
\c tontouma
CREATE EXTENSION IF NOT EXISTS vector;
```
- Appliquez les migrations Alembic (si présentes) ou laissez SQLAlchemy créer au 1er run.
- Lancez le serveur:
```
uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload
```
- Les fichiers audio sont servis sur `http://localhost:9000/uploads/...`.

1-bis) Démarrage des services avec docker-compose (PostgreSQL + MinIO):

Si vous préférez ne pas installer Postgres/pgvector et MinIO localement, utilisez `docker-compose` fourni.

```
docker compose up -d
```

Cela démarre:
- PostgreSQL (pgvector) sur `localhost:5532` (mappé vers 5432 dans le conteneur)
- MinIO API sur `http://localhost:9100`
- MinIO Console sur `http://localhost:9002`
- Un job d'initialisation qui crée le bucket `tontouma-knowledge` et le rend public

Adaptez votre `.env` backend pour pointer vers ces ports:
```
POSTGRES_SERVER=localhost
POSTGRES_PORT=5532
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=tontouma

MINIO_ENDPOINT=localhost:9100
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=tontouma-knowledge
MINIO_SECURE=false
```

Créer l'extension `vector` dans la base (si besoin):
```
docker exec -it tontouma-db psql -U postgres -d tontouma -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

2) Frontend (Next.js):
```
cd front_app
npm install
npm run dev
```
- Ouvrir http://localhost:3000

## Flux fonctionnels
- Chat vocal: upload audio -> transcription (Whisper) -> RAG -> LLM -> TTS -> historique messages (texte+audio)
- Chat texte: saisie front -> RAG -> LLM -> TTS -> historique messages (texte+audio)
- Connaissances (KB): upload fichier (PDF/TXT/…) ou saisie texte -> chunking -> embeddings -> recherche sémantique

## Pages clés (Front)
- `/entity/[id]/test`: test chatbot (audio + texte) avec historique
- `/entity/[id]/knowledge`: gestion de la base de connaissances (upload fichiers + ajout de texte brut)

## Notes
- Orateur (speaker) fixe pour démo: `11111111-1111-1111-1111-111111111111`
- Vérifiez que `uploads/` est créé (le backend le crée si absent) et monté statiquement (voir `app/main.py`).
- MinIO est requis uniquement si vous uploadez des fichiers de connaissance; l’ajout en texte brut fonctionne sans MinIO.

## Dépannage rapide
- Erreurs ASR/Whisper: vérifiez l’installation de `faster-whisper` et les libs CPU.
- TTS gTTS: nécessite un accès réseau pour générer l’audio.
- RAG/Embeddings: le modèle `sentence-transformers` sera téléchargé au premier run (peut être long).
- CORS: sont ouverts par défaut pour le développement.
