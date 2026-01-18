import asyncio
import httpx
import os

# Allow overriding the API URL via environment variable
API_URL = os.environ.get("API_URL", "http://localhost:9000/api/v1")

# System prompt spécifique pour la Mairie
MAIRIE_SYSTEM_PROMPT = """Tu es l'assistant virtuel officiel de la Mairie de Hann Bel Air à Dakar, Sénégal.

COMPORTEMENT GÉNÉRAL:
- Tu réponds aux questions des citoyens concernant les services municipaux
- Tu es professionnel, courtois et serviable
- Tu guides les usagers dans leurs démarches administratives
- IMPORTANT: Ne mets JAMAIS de formattage markdown (pas de gras, pas d'italique, pas d'étoiles *). Le texte sera lu par un outil de synthèse vocale.

SERVICES PRINCIPAUX:
- État Civil (actes de naissance, mariage, décès)
- Urbanisme (permis de construire, autorisations)
- Fiscalité locale (taxes, patentes)
- Action sociale
- Voirie et environnement

Si tu ne connais pas une information précise, invite l'usager à contacter directement la mairie ou à se présenter aux guichets.
"""

ENTITY_DATA = {
    "name": "Mairie Hann Bel Air",
    "description": "Mairie de la commune de Hann Bel Air, arrondissement de Dakar. Services administratifs et municipaux pour les citoyens.",
    "contact_email": "contact@mairie-hannbelair.sn",
    "domain": "Administration Publique"
}

INSTANCES_DATA = [
    {"name": "Guichet Unique", "description": "Accueil principal et orientation des usagers"},
    {"name": "Service État Civil", "description": "Actes de naissance, mariage, décès, légalisations"},
    {"name": "Service Urbanisme", "description": "Permis de construire, certificats d'urbanisme"},
]

DOCUMENTS_DATA = [
    {
        "title": "Présentation Mairie Hann Bel Air",
        "source": "presentation.txt",
        "content": """
# Mairie de Hann Bel Air

## Présentation
La commune de Hann Bel Air est située dans l'arrondissement de Grand Dakar, région de Dakar, Sénégal. 
Elle est connue pour son port de pêche traditionnel de Hann et le célèbre Parc de Hann (zoo de Dakar).

## Adresse
Mairie de Hann Bel Air
Avenue Cheikh Oumar Foutiyou Tall
Hann Bel Air, Dakar
Sénégal

## Horaires d'ouverture
- Lundi à Vendredi: 8h00 - 16h00
- Samedi: Fermé (sauf urgences état civil)
- Dimanche et jours fériés: Fermé

## Contact
- Téléphone: +221 33 832 XX XX
- Email: contact@mairie-hannbelair.sn
"""
    },
    {
        "title": "Service État Civil - Procédures",
        "source": "etat_civil.txt",
        "content": """
# Service État Civil

## Acte de Naissance
### Déclaration de naissance
- Délai: Dans les 30 jours suivant la naissance
- Documents requis: Certificat d'accouchement, pièces d'identité des parents, livret de famille
- Coût: Gratuit

### Copie d'acte de naissance
- Documents: Demande écrite + pièce d'identité
- Délai: 24-48h ouvrables
- Coût: 200 FCFA par copie

## Acte de Mariage
### Célébration de mariage
- Délai de publication des bans: 10 jours minimum
- Documents: Actes de naissance, certificats de résidence, photos d'identité
- Droits de célébration: 5 000 FCFA

## Acte de Décès
- Déclaration dans les 24h
- Documents: Certificat de décès, pièce d'identité du déclarant
- Coût: Gratuit

## Légalisations
- Coût: 200 FCFA par document
- Délai: Immédiat si documents complets
"""
    },
    {
        "title": "Service Urbanisme - Permis et Autorisations",
        "source": "urbanisme.txt",
        "content": """
# Service Urbanisme

## Permis de Construire
### Documents requis
- Demande adressée au Maire
- Titre foncier ou attestation de propriété
- Plan de masse par architecte agréé
- Plan de situation
- 4 jeux de plans architecturaux

### Délai de traitement
- 2 à 3 mois selon complexité du dossier

### Frais
- Variable selon surface: de 50 000 à 500 000 FCFA

## Certificat d'Urbanisme
- Délai: 1 mois
- Coût: 10 000 FCFA
- Validité: 1 an

## Autorisation de Lotir
- Réservé aux terrains non viabilisés
- Dossier technique complet exigé

## Contact Service Urbanisme
- Bureau: 1er étage, Porte 12
- Horaires: 9h-13h, Lundi à Vendredi
"""
    },
    {
        "title": "Fiscalité Locale et Taxes",
        "source": "fiscalite.txt",
        "content": """
# Fiscalité Locale

## Taxes Municipales
### Taxe sur le Foncier Bâti (TFB)
- Base: Valeur locative du bien
- Taux: Variable selon zone
- Paiement: Annuel, avant le 31 mars

### Patente (Activités commerciales)
- Obligatoire pour tout commerce
- Montant selon chiffre d'affaires
- Renouvellement annuel

## Paiement
- Au guichet de la Régie Municipale
- Horaires: 8h30 - 15h30
- Modes: Espèces, chèque certifié

## Attestations fiscales
- Quitus fiscal: 2 000 FCFA
- Délai: 48h ouvrables
"""
    },
    {
        "title": "Services Sociaux et Environnement",
        "source": "social_environnement.txt",
        "content": """
# Action Sociale et Environnement

## Action Sociale
### Aide aux personnes vulnérables
- Demande adressée au service social
- Enquête sociale obligatoire
- Aide ponctuelle ou régulière selon cas

### Bourses scolaires communales
- Dépôt dossiers: Septembre-Octobre
- Critères: Revenus familiaux, résultats scolaires

## Environnement et Cadre de Vie

### Collecte des ordures
- Enlèvement: Lundi, Mercredi, Vendredi
- Plaintes: Service technique (RDC)

### Éclairage public
- Signalement pannes: Service voirie
- Intervention sous 72h

### Espaces verts
- Entretien assuré par la municipalité
- Demandes d'élagage: Formulaire disponible au guichet
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

        print("[Start] Création de l'entité Mairie Hann Bel Air...")

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
            entity_payload = {**ENTITY_DATA, "system_prompt": MAIRIE_SYSTEM_PROMPT}
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

        print("\n" + "="*50)
        print("[Done] Mairie Hann Bel Air créée avec succès !")
        print(f"Entity ID: {entity_id}")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(seed())