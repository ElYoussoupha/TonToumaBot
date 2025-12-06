"""
Script pour lister tous les médecins avec leurs informations
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.crud.crud_appointment import doctor as doctor_crud


async def list_all_doctors():
    """Lister tous les médecins"""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.doctor import Doctor
        from sqlalchemy.orm import selectinload
        
        stmt = select(Doctor).options(selectinload(Doctor.specialty))
        result = await db.execute(stmt)
        doctors = result.scalars().all()
        
        if not doctors:
            print("❌ Aucun médecin trouvé dans la base de données")
            return
        
        print("=" * 80)
        print(f"📋 Liste des médecins ({len(doctors)} trouvé(s))")
        print("=" * 80)
        
        for i, doctor in enumerate(doctors, 1):
            status = "✅ Actif" if doctor.is_active else "❌ Inactif"
            specialty = doctor.specialty.name if doctor.specialty else "Généraliste"
            
            print(f"\n{i}. Dr. {doctor.first_name} {doctor.last_name}")
            print(f"   📧 Email: {doctor.email}")
            print(f"   🏥 Spécialité: {specialty}")
            print(f"   📞 Téléphone: {doctor.phone or 'N/A'}")
            print(f"   ⏱️  Durée consultation: {doctor.consultation_duration} min")
            print(f"   {status}")
            print(f"   🆔 ID: {doctor.doctor_id}")
        
        print("\n" + "=" * 80)
        print("\n💡 Pour réinitialiser un mot de passe:")
        print("   python scripts/reset_doctor_password.py <email>")


if __name__ == "__main__":
    asyncio.run(list_all_doctors())
