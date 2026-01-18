import asyncio
import httpx
import os

# Allow overriding the API URL via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:9000/api/v1")

# System prompt spécifique pour JOJ 2026 - Assistant Stade Abdoulaye Wade
JOJ_SYSTEM_PROMPT = """Tu es l'assistant virtuel officiel des Jeux Olympiques de la Jeunesse (JOJ) Dakar 2026, basé au Stade Abdoulaye Wade de Diamniadio.

CONTEXTE DE L'ÉVÉNEMENT:
- Les JOJ Dakar 2026 sont le premier événement olympique en Afrique.
- Dates : du 31 octobre au 13 novembre 2026.
- Devise : "L'Afrique accueille, Dakar célèbre".
- Lieux : Dakar, Diamniadio et Saly.

TA LOCALISATION - STADE ABDOULAYE WADE (DIAMNIADIO):
- Tu te trouves physiquement au Stade Abdoulaye Wade.
- C'est un stade moderne de 50 000 places, inauguré en 2022.
- Il accueillera la cérémonie d'ouverture et les épreuves d'athlétisme.

TES MISSIONS:
1. Accueillir les visiteurs du stade et les fans du monde entier.
2. Donner des informations sur le programme, les sports et les sites.
3. Partager les valeurs olympiques : Excellence, Amitié, Respect.
4. Expliquer l'esprit "Teranga" (hospitalité sénégalaise).

COMPORTEMENT:
- Tu es chaleureux, dynamique et fier de représenter le Sénégal et l'Afrique.
- Tu parles français (langue officielle) et tu peux utiliser quelques expressions Wolof pour la convivialité (Nanga def, Jamm rek).
- Si on te demande le programme détaillé jour par jour, précise qu'il est "à venir" mais donne les dates générales.
- IMPORTANT: Ne mets JAMAIS de formattage markdown (pas de gras, pas d'italique, pas d'étoiles *). Le texte sera lu par un outil de synthèse vocale.
"""

ENTITY_DATA = {
    "name": "JOJ Dakar 2026",
    "description": "Jeux Olympiques de la Jeunesse - Dakar 2026. Du 31 oct au 13 nov 2026. Premier événement olympique en Afrique.",
    "contact_email": "contact@dakar2026.sn",
    "domain": "Sport / Événementiel",
    "custom_dashboard_component": "joj2026"
}

INSTANCES_DATA = [
    {"name": "Assistant Stade Abdoulaye Wade", "description": "Assistant virtuel principal basé au Stade Olympique", "location": "Diamniadio"},
    {"name": "Info Village Olympique", "description": "Pour les athlètes et délégations", "location": "Campus Diamniadio"},
]

# Documents KB
DOCUMENTS_DATA = [
    {
        "title": "Présentation JOJ Dakar 2026",
        "source": "presentation_joj.txt",
        "content": """
# JOJ Dakar 2026 - L'Afrique accueille, Dakar célèbre

## Une première historique
Les Jeux Olympiques de la Jeunesse de Dakar 2026 seront le premier événement olympique jamais organisé sur le continent africain.
Ils se tiendront du 31 octobre au 13 novembre 2026.
Ces jeux sont un catalyseur pour la transformation du Sénégal par le sport et une source d'inspiration pour la jeunesse africaine.

## Vision et Valeurs
- Vision : Jeunesse et Sport comme vecteurs de paix et de développement.
- Valeurs Olympiques : Excellence, Amitié, Respect.
- Valeurs Locales : Teranga (Hospitalité), Civisme, Citoyenneté.
"""
    },
    {
        "title": "Sites et Lieux de Compétition",
        "source": "sites_competitions.txt",
        "content": """
# Sites des JOJ Dakar 2026

Les compétitions se dérouleront sur trois zones principales :

## 1. Dakar (Centre-ville et environs)
- Tour de l'Œuf : Basketball 3x3, Breaking, Skateboard, Baseball5.
- Stade Iba Mar Diop : Athlétisme, Rugby à 7, Football (Futsal).
- Corniche Ouest / Plage : Sports nautiques, Cyclisme sur route.
- Arène Nationale (Lutte) : Wushu, Boxe.

## 2. Diamniadio (Ville nouvelle)
- Stade Abdoulaye Wade : Cérémonie d'ouverture, Athlétisme.
- Dakar Arena : Handball, Gymnastique.
- Centre des Expositions : Escrime, Tennis de Table, Badminton.
- Village Olympique : Campus Universitaire Amadou Mahtar Mbow.

## 3. Saly (Station balnéaire)
- Plage et Golf de Saly : Voile, Beach Volley, Golf, Surf (si conditions).
"""
    },
    {
        "title": "Liste des Sports - Programme Sportif",
        "source": "sports_list.txt",
        "content": """
# Programme Sportif JOJ 2026

Le programme comprend 25 sports de compétition et 10 sports d'engagement.
Égalité parfaite : autant d'hommes que de femmes athlètes.

## 25 Sports de Compétition
1. Athlétisme
2. Aviron (mer)
3. Badminton
4. Baseball5
5. Basketball 3x3
6. Boxe
7. Breaking (Danse)
8. Cyclisme (Route)
9. Escrime
10. Football (Futsal)
11. Gymnastique
12. Handball (Beach)
13. Judo
14. Lutte (Plage)
15. Rugby à 7
16. Skateboard
17. Natation / Plongeon
18. Sports Équestres (Saut)
19. Taekwondo
20. Tennis de Table
21. Tir à l'arc
22. Triathlon
23. Voile
24. Volleyball (Beach)
25. Wushu

## 10 Sports d'Engagement (Démonstration/Initiation)
Canoë-kayak, Escalade, Golf, Haltérophilie, Hockey, Karaté, Pentathlon moderne, Surf, Tennis, Tir.
"""
    }
]

async def wait_for_server(client):
    print("[Wait] Waiting for server to be ready...")
    for i in range(10):
        try:
            base = API_URL.rstrip('/')
            docs_url = base.replace('/api/v1', '') + '/docs'
            response = await client.get(docs_url)
            if response.status_code == 200:
                print("[OK] Server is ready!")
                return True
        except Exception:
            pass
        await asyncio.sleep(2)
    print("[Error] Server is not responding.")
    return False

async def seed():
    async with httpx.AsyncClient(timeout=180.0) as client:
        if not await wait_for_server(client):
            return

        print("[Start] Création de l'entité JOJ Dakar 2026...")

        # 1. Check if Entity already exists
        entity_id = None
        try:
            response = await client.get(f"{API_URL}/entities")
            if response.status_code == 200:
                entities = response.json()
                for ent in entities:
                    if ent.get("name") == ENTITY_DATA["name"]:
                        entity_id = ent.get("entity_id")
                        print(f"[Skip] Entity '{ENTITY_DATA['name']}' already exists with ID: {entity_id}")
                        break
        except Exception as e:
            print(f"[Warn] Could not check existing entities: {e}")

        # Create entity if not exists
        if not entity_id:
            entity_payload = {**ENTITY_DATA, "system_prompt": JOJ_SYSTEM_PROMPT}
            print(f"Creating Entity: {entity_payload['name']}...")
            
            try:
                response = await client.post(f"{API_URL}/entities", json=entity_payload)
                
                if response.status_code not in [200, 201]:
                    print(f"[Error] Failed to create entity: {response.text}")
                    return

                entity = response.json()
                entity_id = entity.get("entity_id")
                print(f"[OK] Entity created with ID: {entity_id}")
            except Exception as e:
                print(f"[Error] Exception creating entity: {e}")
                return

        # 2. Get existing instances for this entity
        existing_instances = set()
        try:
            response = await client.get(f"{API_URL}/instances")
            if response.status_code == 200:
                for inst in response.json():
                    if inst.get("entity_id") == entity_id:
                        existing_instances.add(inst.get("name"))
        except Exception:
            pass

        # Create Instances (skip if exists)
        print("\nCreating Instances...")
        for inst_data in INSTANCES_DATA:
            if inst_data["name"] in existing_instances:
                print(f"  [Skip] Instance already exists: {inst_data['name']}")
                continue
            
            inst_payload = {**inst_data, "entity_id": entity_id, "status": "active"}
            response = await client.post(f"{API_URL}/instances", json=inst_payload)
            if response.status_code in [200, 201]:
                print(f"  [OK] Created instance: {inst_data['name']}")
            else:
                print(f"  [Error] Failed to create instance {inst_data['name']}: {response.text}")

        # 3. Get existing documents for this entity
        existing_docs = set()
        try:
            response = await client.get(f"{API_URL}/kb/documents/{entity_id}")
            if response.status_code == 200:
                for doc in response.json():
                    existing_docs.add(doc.get("title"))
        except Exception:
            pass

        # Create Documents (skip if exists)
        print("\nAdding Documents to Knowledge Base...")
        total_docs = len(DOCUMENTS_DATA)
        for idx, doc_data in enumerate(DOCUMENTS_DATA, 1):
            if doc_data["title"] in existing_docs:
                print(f"  [Skip] ({idx}/{total_docs}) Document already exists: {doc_data['title']}")
                continue
            
            print(f"  [{idx}/{total_docs}] Processing: {doc_data['title']}...", end=" ", flush=True)
            
            file_content = doc_data["content"].encode('utf-8')
            files = {
                "file": (doc_data["source"], file_content, "text/plain")
            }
            data = {
                "title": doc_data["title"],
                "entity_id": str(entity_id)
            }
            
            try:
                response = await client.post(f"{API_URL}/kb/documents", data=data, files=files)
                if response.status_code in [200, 201]:
                    print("OK")
                else:
                    print(f"FAILED - {response.text[:100]}")
            except Exception as e:
                print(f"ERROR - {str(e)[:50]}")

        print("\n" + "="*60)
        print("[Done] JOJ Dakar 2026 configuré avec succès !")
        print(f"Entity ID: {entity_id}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(seed())
