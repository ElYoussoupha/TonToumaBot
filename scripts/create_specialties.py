"""
Script pour créer les spécialités médicales de base
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.crud.crud_appointment import specialty as specialty_crud
from app.schemas.specialty import SpecialtyCreate


SPECIALTIES = [
    {
        "name": "Généraliste",
        "description": "Médecine générale - Consultation et suivi médical général"
    },
    {
        "name": "Pédiatre",
        "description": "Spécialiste de la santé des enfants et adolescents"
    },
    {
        "name": "Dentiste",
        "description": "Soins dentaires et santé bucco-dentaire"
    },
    {
        "name": "Neurologue",
        "description": "Spécialiste du système nerveux et des troubles neurologiques"
    },
    {
        "name": "Cardiologue",
        "description": "Spécialiste du cœur et du système cardiovasculaire"
    },
    {
        "name": "Dermatologue",
        "description": "Spécialiste de la peau, des cheveux et des ongles"
    },
    {
        "name": "Ophtalmologue",
        "description": "Spécialiste des yeux et de la vision"
    }
]


async def create_specialties():
    """Créer les spécialités dans la base de données"""
    async with AsyncSessionLocal() as db:
        created_count = 0
        skipped_count = 0
        
        print("🏥 Création des spécialités médicales...\n")
        
        for spec_data in SPECIALTIES:
            # Vérifier si la spécialité existe déjà
            existing = await specialty_crud.get_by_name(db=db, name=spec_data["name"])
            
            if existing:
                print(f"⏭️  {spec_data['name']} - Déjà existante (ID: {existing.specialty_id})")
                skipped_count += 1
            else:
                # Créer la spécialité
                specialty_in = SpecialtyCreate(**spec_data)
                specialty = await specialty_crud.create(db=db, obj_in=specialty_in)
                print(f"✅ {spec_data['name']} - Créée (ID: {specialty.specialty_id})")
                created_count += 1
        
        print(f"\n📊 Résumé:")
        print(f"   - Créées: {created_count}")
        print(f"   - Déjà existantes: {skipped_count}")
        print(f"   - Total: {len(SPECIALTIES)}")


if __name__ == "__main__":
    print("=" * 60)
    print("Script de création des spécialités médicales")
    print("=" * 60 + "\n")
    
    try:
        asyncio.run(create_specialties())
        print("\n✅ Script terminé avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
