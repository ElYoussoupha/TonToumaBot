import asyncio
import httpx
import os

# Allow overriding the API URL via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:9000/api/v1")

# System prompt spécifique pour Guichet Unique - Sénégal Services
GUICHET_SYSTEM_PROMPT = """Tu es l'assistant virtuel officiel de Sénégal Services (Guichet Unique Administratif).
Ton rôle est d'aider les citoyens sénégalais et les étrangers résidents à effectuer leurs démarches administratives.

TES MISSIONS:
1. Informer sur les procédures administratives (pièces à fournir, coûts, lieux de dépôt).
2. Orienter vers les services compétents (Espaces Sénégal Services, Commissariats, Tribunaux).
3. Expliquer le fonctionnement de la plateforme numérique "senegalservices.sn".
4. Simplifier le langage administratif pour qu'il soit compréhensible par tous.

TON COMPORTEMENT:
- Tu es professionnel, courtois, précis et serviable.
- Tu parles un français administratif clair. Tu comprends le Wolof mais tu réponds principalement en français (sauf si l'utilisateur insiste).
- Si tu ne connais pas une procédure spécifique, conseille de se rendre dans l'Espace Sénégal Services le plus proche.
- Ne donne pas de conseils juridiques complexes, limite-toi aux procédures administratives standard.
- IMPORTANT: Ne mets JAMAIS de formattage markdown (pas de gras, pas d'italique). Le texte sera lu par un outil de synthèse vocale.

DÉMARCHES FRÉQUENTES:
- Passeport et Carte d'Identité (CNI).
- Casier Judiciaire.
- Actes d'état civil (Naissance, Mariage).
- Permis de construire.
"""

ENTITY_DATA = {
    "name": "Guichet Unique Administratif",
    "description": "Sénégal Services - Simplification et dématérialisation des démarches administratives pour les citoyens et les entreprises.",
    "contact_email": "contact@senegalservices.sn",
    "domain": "Administration / Service Public",
    "custom_dashboard_component": "guichet_unique"
}

INSTANCES_DATA = [
    {"name": "Portail Numérique Sénégal Services", "description": "Assistant en ligne du portail senegalservices.sn", "location": "Virtuel"},
    {"name": "Espace Sénégal Services Dakar", "description": "Guichet physique Département de Dakar", "location": "Dakar"},
    {"name": "Application Mobile", "description": "Assistant intégré à l'application mobile Sénégal Services", "location": "Mobile"},
]

# Documents KB
DOCUMENTS_DATA = [
    {
        "title": "Présentation Sénégal Services",
        "source": "presentation_senegal_services.txt",
        "content": """
# Présentation de Sénégal Services

Sénégal Services est le dispositif de l'État du Sénégal pour rapprocher l'administration des usagers.
Il repose sur deux piliers :
1. Le portail numérique senegalservices.sn : pour s'informer et faire ses démarches en ligne 24h/24.
2. Les Espaces Sénégal Services (ESS) : des guichets uniques physiques présents dans les 46 départements du pays.

## Objectifs
- Simplifier les procédures.
- Réduire les délais de traitement.
- Éviter les déplacements inutiles grâce au numérique.
- Offrir un accompagnement de proximité.
"""
    },
    {
        "title": "Demande de Passeport Ordinaire",
        "source": "procedure_passeport.txt",
        "content": """
# Demande de Passeport Ordinaire Numérisé

## Pièces à fournir :
1. Une demande adressée au Ministre de l'Intérieur.
2. La Carte Nationale d'Identité Biométique (original + photocopie).
3. Un timbre fiscal de 20 000 FCFA (achat possible en ligne ou via Quittance Direction de l'Enregistrement).
4. Pour les mineurs : une autorisation parentale légalisée.

## Lieu de dépôt :
- Direction de la Police des Étrangers et des Titres de Voyage (DPETV) à Dieuppeul.
- Espaces Sénégal Services (pour l'enrôlement ou l'orientation).
- Commissariats de police habilités.

## Validité :
- 5 ans pour les passeports ordinaires.
- 10 ans possible selon les nouvelles dispositions (à vérifier).

## Coût :
- 20 000 FCFA de timbre fiscal.
"""
    },
    {
        "title": "Carte Nationale d'Identité (CNI CEDEAO)",
        "source": "procedure_cni.txt",
        "content": """
# Demande de Carte Nationale d'Identité (CNI) CEDEAO

## Pièces à fournir :
1. Un extrait de naissance de moins de 3 mois OU l'ancienne carte d'identité.
2. Un certificat de résidence (pour la première demande ou changement d'adresse).
3. Présence physique obligatoire pour la prise d'empreintes (biométrie).

## Coût :
- Gratuit pour la première demande (établissement).
- 10 000 FCFA pour un duplicata (en cas de perte).

## Validité :
- 10 ans.

## Lieu de dépôt :
- Commissariats de police.
- Brigades de gendarmerie.
- Sous-préfectures.
"""
    },
    {
        "title": "Extrait de Casier Judiciaire",
        "source": "procedure_casier_judiciaire.txt",
        "content": """
# Demande d'Extrait de Casier Judiciaire

## Procédure :
1. Se rendre au Greffe du Tribunal de Grande Instance ou d'Instance de son lieu de naissance.
2. Munir de sa Carte Nationale d'Identité et d'un extrait de naissance.
3. Paiement d'une taxe (généralement 200 à 500 FCFA selon le tribunal).

## En ligne :
- Il est possible de faire la demande sur senegalservices.sn pour certains tribunaux interconnectés.
- Le document peut être retiré dans un Espace Sénégal Services ou envoyé par la poste (optionnel).

## Validité :
- 3 mois.
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

        print("[Start] Création de l'entité Guichet Unique Administratif...")

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
            entity_payload = {**ENTITY_DATA, "system_prompt": GUICHET_SYSTEM_PROMPT}
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
        print("[Done] Guichet Unique Administratif configuré avec succès !")
        print(f"Entity ID: {entity_id}")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(seed())
