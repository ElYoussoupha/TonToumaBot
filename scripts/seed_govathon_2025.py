import asyncio
import httpx
import os

# Allow overriding the API URL via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:9000/api/v1")

# System prompt spécifique pour GOVATHON 2025
GOVATHON_SYSTEM_PROMPT = """Tu es l'assistant virtuel officiel du GOVATHON 2025, le grand hackathon gouvernemental du Sénégal.

CONTEXTE DE L'ÉVÉNEMENT:
- Le GOVATHON 2025 est la 2ème édition du hackathon gouvernemental du Sénégal
- Organisé par le Ministère de la Fonction Publique et le Ministère de la Communication, des Télécommunications et du Numérique
- Finale le 23 décembre 2025 au CICAD de Diamniadio, Dakar
- 104 équipes finalistes sélectionnées parmi 812 projets soumis
- Prix allant jusqu'à 20 000 000 FCFA pour les gagnants

LIEU - CICAD DIAMNIADIO:
- Centre International de Conférences Abdou Diouf (CICAD)
- Situé à Diamniadio, Dakar, Sénégal
- Accessible via l'autoroute à péage Dakar-Diamniadio

TES MISSIONS:
1. Informer les visiteurs et participants sur le programme et le planning de l'événement
2. Orienter les gens dans le CICAD (salles, stands, services)
3. Présenter les équipes compétitrices et leurs projets
4. Donner des infos logistiques (horaires, restauration, accès WiFi, etc.)

COMPORTEMENT:
- Sois enthousiaste et professionnel
- Encourage l'innovation et la transformation numérique
- Si tu ne connais pas une information précise, invite l'utilisateur à se renseigner au stand d'accueil
- IMPORTANT: Ne mets JAMAIS de formattage markdown (pas de gras, pas d'italique, pas d'étoiles *). Le texte sera lu par un outil de synthèse vocale.

Vive l'innovation sénégalaise ! 🇸🇳
"""

ENTITY_DATA = {
    "name": "GOVATHON 2025",
    "description": "Hackathon gouvernemental du Sénégal - 2ème édition. Finale au CICAD Diamniadio le 23 décembre 2025. 104 équipes finalistes en compétition pour des prix allant jusqu'à 20M FCFA.",
    "contact_email": "contact@govathon.sn",
    "domain": "Événementiel / Tech",
    "custom_dashboard_component": "govathon"
}

INSTANCES_DATA = [
    {"name": "Accueil Principal", "description": "Point d'information général et orientation des visiteurs"},
    {"name": "Zone Compétition", "description": "Espace dédié aux équipes finalistes et jurys"},
    {"name": "Espace Visiteurs", "description": "Zone grand public et networking"},
]

# Documents KB de base (l'utilisateur ajoutera le contenu détaillé après)
DOCUMENTS_DATA = [
    {
        "title": "Présentation GOVATHON 2025",
        "source": "presentation_govathon.txt",
        "content": """
# GOVATHON 2025 - Hackathon Gouvernemental du Sénégal

## Qu'est-ce que le GOVATHON ?
Le GOVATHON est le plus grand hackathon gouvernemental du Sénégal, organisé dans le cadre du "New Deal Technologique". 
Il vise à mobiliser les jeunes talents, étudiants, startups et chercheurs pour développer des solutions numériques innovantes au service de l'administration publique.

## GOVATHON 2025 - 2ème Édition
- Date de la finale : 23 décembre 2025
- Lieu : CICAD Diamniadio, Dakar
- 812 projets soumis
- 104 équipes finalistes sélectionnées
- Prix : Jusqu'à 20 000 000 FCFA

## Organisateurs
- Ministère de la Fonction Publique, du Travail et de la Réforme du Service Public
- Ministère de la Communication, des Télécommunications et du Numérique

## Objectifs
- Accélérer la digitalisation des services publics
- Détecter les jeunes talents du numérique
- Promouvoir l'auto-entrepreneuriat tech
- Renforcer la collaboration entre administration et écosystème numérique
"""
    },
    {
        "title": "CICAD Diamniadio - Informations Pratiques",
        "source": "cicad_info.txt",
        "content": """
# Centre International de Conférences Abdou Diouf (CICAD)

## Localisation
Le CICAD est situé à Diamniadio, à environ 30 km de Dakar.
Adresse : Pôle Urbain de Diamniadio, Sénégal

## Accès
- Par autoroute à péage : Prendre la direction Diamniadio, sortie CICAD
- Transport en commun : Navettes spéciales depuis Dakar le jour de l'événement
- Covoiturage recommandé

## Services sur place
- Parking gratuit
- Restauration disponible
- WiFi gratuit
- Toilettes accessibles
- Espace prière

## Plan du CICAD pour GOVATHON 2025
- Hall Principal : Accueil et enregistrement
- Salle de Conférence : Cérémonies et pitchs
- Zone d'Exposition : Stands des équipes finalistes
- Espace Networking : Rencontres B2B
"""
    },
    {
        "title": "Plan des Stands - Finale Govathon 2025",
        "source": "plan_stands.txt",
        "content": """
# Plan des Stands - Finale Govathon 2025

## CONSIGNES D'ORIENTATION (IMPORTANT)
Quand tu donnes une position, NE DONNE PAS LE NUMÉRO DU STAND (ex: "Stand 3").
UTILISE UNIQUEMENT DES DESCRIPTIONS RELATIVES ET NATURELLES comme :
- "C'est le 3ème stand sur la gauche en partant de l'entrée."
- "C'est juste en face de nous."
- "C'est le stand juste après la porte Administration."
- "C'est le 7ème sur la droite."
- "C'est entre X et Y."

## NOTRE POSITION (Tontouma Bot)
Nous sommes le **3ème stand sur la droite** en venant de l'entrée.
Entourés par AgriDataGov (avant) et Ecobox Innov (après).

## CÔTÉ DROIT (En partant de l'entrée)
1. SunuMarket (1er à droite)
2. AgriDataGov (2ème à droite)
3. **Tontouma Bot** (NOUS SOMMES ICI - 3ème à droite)
4. Ecobox Innov (4ème à droite)
5. [Repère: Porte Administration]
6. Kay bay (Juste après la porte Administration, 5ème à droite)
7. Ecolo (6ème à droite)
8. Pass bi (7ème à droite)
9. Sunu peche net (8ème à droite)
10. Green Sponge (9ème à droite, dernier)

## CÔTÉ GAUCHE (En partant de l'entrée)
1. Kaysigne (1er à gauche)
2. Paysettal (2ème à gauche)
3. E-sante (3ème à gauche, approx. en face de nous)
4. Minewatch Senegal (4ème à gauche)
5. i-ticket (5ème à gauche - Concurrent direct)
6. Kaarange (6ème à gauche)
7. Eyedentify (7ème à gauche)
8. Salin Smart (8ème à gauche)
9. Sotilma (9ème à gauche)
10. (Stand inconnu / X) (10ème à gauche)
11. Africa velocity groupe (11ème à gauche, dernier)
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

        print("[Start] Création de l'entité GOVATHON 2025...")

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
            entity_payload = {**ENTITY_DATA, "system_prompt": GOVATHON_SYSTEM_PROMPT}
            print(f"Creating Entity: {entity_payload['name']}...")
            
            try:
                response = await client.post(f"{API_URL}/entities", json=entity_payload)
                print(f"[DEBUG] POST {API_URL}/entities -> status {response.status_code}")
                
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
            
            inst_payload = {**inst_data, "entity_id": entity_id}
            response = await client.post(f"{API_URL}/instances", json=inst_payload)
            if response.status_code in [200, 201]:
                print(f"  [OK] Created instance: {inst_data['name']}")
            else:
                print(f"  [Error] Failed to create instance {inst_data['name']}: {response.text}")

        # 3. Get existing documents for this entity
        existing_docs = {}
        try:
            response = await client.get(f"{API_URL}/kb/documents/{entity_id}")
            if response.status_code == 200:
                for doc in response.json():
                    existing_docs[doc.get("title")] = doc.get("doc_id")
        except Exception:
            pass

        # Create Documents (skip if exists)
        print("\nAdding Documents to Knowledge Base...")
        total_docs = len(DOCUMENTS_DATA)
        for idx, doc_data in enumerate(DOCUMENTS_DATA, 1):
            # Special handling for 'Plan des Stands': if it exists, delete it first to allow update
            if doc_data["title"] == "Plan des Stands - Finale Govathon 2025" and doc_data["title"] in existing_docs:
                print(f"  [Update] Deleting existing '{doc_data['title']}' to update content...")
                try:
                    del_res = await client.delete(f"{API_URL}/kb/documents/{existing_docs[doc_data['title']]}")
                    if del_res.status_code == 200:
                        print("  [OK] Deleted.")
                    else:
                        print(f"  [Error] Delete failed: {del_res.status_code}")
                except Exception as e:
                    print(f"  [Error] Delete exception: {e}")
            elif doc_data["title"] in existing_docs:
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
        print("[Done] GOVATHON 2025 créé avec succès !")
        print(f"Entity ID: {entity_id}")
        print("="*60)
        print("\nLe bot est prêt ! Tu peux maintenant ajouter des documents")
        print("supplémentaires (équipes, stands, planning détaillé) via")
        print("l'interface KB de cette entité.")

if __name__ == "__main__":
    asyncio.run(seed())