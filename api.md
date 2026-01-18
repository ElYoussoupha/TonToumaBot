# API Reference & Guide d'Intégration

Base URL: `http://localhost:9000/api/v1`

## 📚 Guide d'Intégration Rapide

Ce guide explique comment connecter une application tierce (frontend, widget, borne interactive) au backend TonToumaBot.

### Étape 1 : Identifier ou Créer une Instance
Chaque chatbot est lié à une **Instance** (qui appartient à une **Entité**).

#### GET /instances
Récupère la liste des instances disponibles.
**Response Example:**
```json
[
  {
    "instance_id": "550e8400-e29b-41d4-a716-446655440000",
    "entity_id": "770e8400-e29b-41d4-a716-446655440000",
    "name": "Accueil Principal",
    "location": "Dakar",
    "status": "active",
    "api_key": "..."
  }
]
```
> **ID Important** : Sauvegardez le champ `instance_id`. Il sera requis pour toutes les interactions de chat.

### Étape 2 : Initialiser une Session
Pour maintenir le contexte de la conversation (historique des échanges), vous devez créer ou identifier une session.

#### POST /chat/sessions
Crée une nouvelle session de chat.
**Request Body:**
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
**Response Example:**
```json
{
  "success": true,
  "session_id": "880e8400-e29b-41d4-a716-446655440000",
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

### Étape 3 : Échanger des Messages

#### POST /chat/text
Envoyer un message texte.
**Request Body:**
```json
{
  "instance_id": "550e8400-e29b-41d4-a716-446655440000",
  "text": "Bonjour, quels sont les horaires ?",
  "session_id": "880e8400-e29b-41d4-a716-446655440000",
  "forced_language": "fr" // Optionnel: "fr", "wo", "en"
}
```
**Response Example:**
```json
{
  "session_id": "880e8400-e29b-41d4-a716-446655440000",
  "transcription": "Bonjour, quels sont les horaires ?",
  "response_text": "Nous sommes ouverts de 8h à 18h.",
  "response_audio": "/uploads/audio_response_123.wav",
  "detected_language": "fr"
}
```

#### POST /chat/messages
Envoyer un message vocal (Multipart Form Data).
**FormData:**
- `instance_id`: "550e8400-e29b-41d4-a716-446655440000"
- `audio_file`: [Fichier binaire .wav/.mp3]
- `session_id`: "880e8400-e29b-41d4-a716-446655440000"
- `forced_language`: "wo" (Optionnel)

**Response Example:**
```json
{
  "session_id": "880e8400-e29b-41d4-a716-446655440000",
  "transcription": "Naka suba ci ?",
  "response_text": "Jamm rek, alhamdulillah.",
  "response_audio": "/uploads/audio_response_456.wav",
  "detected_language": "wo"
}
```

---

## 📖 Référence Complète

### Authentication
Aucune (Mode Développement). Les CORS sont ouverts.

### Entities & Instances

#### GET /entities
Lister les organisations.
**Response Example:**
```json
[
  {
    "entity_id": "uuid",
    "name": "Clinique des Mamelles",
    "description": "Clinique privée..."
  }
]
```

#### GET /chat/sessions
Lister l'historique des sessions pour une instance.
**Query Param**: `?instance_id={uuid}`
**Response Example:**
```json
[
  {
    "session_id": "uuid",
    "created_at": "2023-10-27T10:00:00",
    "message_count": 5,
    "preview": "Bonjour, je voudrais prendre rendez-vous..."
  }
]
```

---

### Medical & Appointments

#### GET /appointments/available
Rechercher des créneaux.
**Query Params**: `entity_id={uuid}&date=2023-12-25&specialty_id={uuid}`
**Response Example:**
```json
{
  "success": true,
  "slots": [
    {
      "doctor_id": "uuid",
      "doctor_name": "Dr. Diop",
      "date": "2023-12-25",
      "start_time": "09:00",
      "end_time": "09:30"
    }
  ]
}
```

#### POST /appointments/book
Réserver un créneau.
**Request Body:**
```json
{
  "doctor_id": "uuid",
  "date": "2023-12-25",
  "time": "09:00",
  "patient_name": "Moussa Diouf",
  "patient_phone": "771234567",
  "reason": "Consultation générale",
  "session_id": "uuid"
}
```