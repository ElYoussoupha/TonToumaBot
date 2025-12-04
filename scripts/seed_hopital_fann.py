import asyncio
import httpx
import json
from uuid import UUID

API_URL = "http://localhost:9000/api/v1"

# Data to seed
ENTITY_DATA = {
    "name": "Hôpital Fann de Dakar",
    "description": "Centre Hospitalier National Universitaire de Fann. Spécialisé en neurologie, pneumologie et maladies infectieuses.",
    "contact_email": "contact@hopital-fann.sn"
}

INSTANCES_DATA = [
    {"name": "Accueil Principal", "location": "Entrée Principale - Guichet 1", "status": "active"},
    {"name": "Secrétariat Neurologie", "location": "Bâtiment Neurologie - 1er étage", "status": "active"},
    {"name": "Urgences", "location": "Aile Ouest", "status": "active"},
    {"name": "Service Pneumologie", "location": "Pavillon Pneumo", "status": "maintenance"}
]

DOCUMENTS_DATA = [
    {
        "title": "Guide du Patient - Admission",
        "source": "guide_patient_2024.pdf",
        "content": """
        # Guide d'Admission - Hôpital Fann

        ## Horaires des visites
        Les visites sont autorisées de 13h00 à 15h00 et de 18h00 à 20h00 tous les jours.
        Pour les services de réanimation, les visites sont limitées à 1 personne de 13h à 14h.

        ## Documents requis pour l'admission
        1. Pièce d'identité nationale ou passeport en cours de validité.
        2. Lettre de liaison du médecin traitant (si référé).
        3. Carte d'assurance maladie ou prise en charge (IPM, imputations budgétaires).
        4. Carnet de santé.

        ## Tarifs des consultations (Indicatif)
        - Consultation Généraliste : 5 000 FCFA
        - Consultation Spécialiste : 10 000 FCFA
        - Urgences : 3 000 FCFA (Ticket modérateur)

        ## Services disponibles
        - Neurologie
        - Pneumologie
        - Maladies Infectieuses
        - Cardiologie
        - Psychiatrie
        - Radiologie et Imagerie Médicale
        """
    },
    {
        "title": "Préparation Examen Scanner",
        "source": "protocole_scanner.docx",
        "content": """
        # Protocole de Préparation pour Examen Scanner (TDM)

        ## Avant l'examen
        - **Jeûne** : Il est demandé d'être à jeun 4 heures avant l'examen si une injection de produit de contraste est prévue.
        - **Allergies** : Signalez impérativement toute allergie connue, notamment à l'iode.
        - **Insuffisance rénale** : Un bilan sanguin (Créatinine) récent (moins de 1 mois) est obligatoire pour les patients de plus de 60 ans ou diabétiques.

        ## Déroulement
        L'examen dure environ 10 à 15 minutes. Vous serez allongé sur une table qui se déplace à l'intérieur de l'anneau. Il est important de rester immobile.

        ## Après l'examen
        Si vous avez reçu une injection, buvez beaucoup d'eau (1,5L) dans la journée pour éliminer le produit.
        """
    },
    {
        "title": "Service de Neurologie - Informations",
        "source": "brochure_neuro.txt",
        "content": """
        # Service de Neurologie - CHNU Fann

        Le service de neurologie de Fann est une référence en Afrique de l'Ouest.

        ## Pathologies traitées
        - Accidents Vasculaires Cérébraux (AVC)
        - Épilepsie
        - Maladie de Parkinson
        - Sclérose en plaques
        - Neuropathies périphériques

        ## Équipe médicale
        Chef de Service : Pr. [Nom Fictif]
        L'équipe est composée de 15 neurologues, 20 infirmiers spécialisés et 5 kinésithérapeutes.

        ## Prise de rendez-vous
        Les rendez-vous se prennent au guichet des consultations externes du lundi au vendredi de 8h à 12h.
        Téléphone secrétariat : 33 800 00 00
        """
    }
]

async def seed():
    async with httpx.AsyncClient() as client:
        print("🚀 Démarrage du script de seed...")

        # 1. Create Entity
        print(f"Creating Entity: {ENTITY_DATA['name']}...")
        response = await client.post(f"{API_URL}/entities", json=ENTITY_DATA)
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create entity: {response.text}")
            return
        
        entity = response.json()
        entity_id = entity["entity_id"]
        print(f"✅ Entity created with ID: {entity_id}")

        # 2. Create Instances
        print("\nCreating Instances...")
        for inst_data in INSTANCES_DATA:
            inst_payload = {**inst_data, "entity_id": entity_id}
            response = await client.post(f"{API_URL}/instances", json=inst_payload)
            if response.status_code in [200, 201]:
                print(f"  ✅ Created instance: {inst_data['name']}")
            else:
                print(f"  ❌ Failed to create instance {inst_data['name']}: {response.text}")

        # 3. Create Documents
        print("\nAdding Documents to Knowledge Base...")
        for doc_data in DOCUMENTS_DATA:
            doc_payload = {
                "title": doc_data["title"],
                "source": doc_data["source"],
                "content": doc_data["content"],
                "entity_id": entity_id
            }
            # Note: We use the /documents endpoint directly for text content
            # The /upload endpoint is for multipart files
            response = await client.post(f"{API_URL}/kb/documents", json=doc_payload)
            if response.status_code in [200, 201]:
                print(f"  ✅ Added document: {doc_data['title']}")
            else:
                print(f"  ❌ Failed to add document {doc_data['title']}: {response.text}")

        print("\n✨ Seeding terminé avec succès !")

if __name__ == "__main__":
    asyncio.run(seed())
