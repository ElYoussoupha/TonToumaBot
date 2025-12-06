"""
Script pour réinitialiser le mot de passe d'un médecin
"""
import asyncio
import sys
import secrets
import hashlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.crud.crud_appointment import doctor as doctor_crud


async def reset_doctor_password(email: str):
    """Réinitialiser le mot de passe d'un médecin"""
    async with AsyncSessionLocal() as db:
        # Trouver le médecin
        doctor = await doctor_crud.get_by_email(db=db, email=email)
        
        if not doctor:
            print(f"❌ Aucun médecin trouvé avec l'email: {email}")
            return
        
        # Générer nouveau mot de passe
        new_password = secrets.token_urlsafe(12)
        
        # Hasher le mot de passe (même format que doctors.py)
        salt = secrets.token_hex(16)
        password_with_salt = f"{new_password}{salt}"
        password_hash = hashlib.sha256(password_with_salt.encode()).hexdigest()
        full_hash = f"{salt}${password_hash}"  # Utiliser $ comme séparateur
        
        # Mettre à jour
        doctor.password_hash = full_hash
        await db.commit()
        
        print("=" * 60)
        print(f"✅ Mot de passe réinitialisé pour Dr. {doctor.first_name} {doctor.last_name}")
        print("=" * 60)
        print(f"\n📧 Email: {doctor.email}")
        print(f"🔑 Nouveau mot de passe: {new_password}")
        print(f"\n⚠️  Communiquez ce mot de passe au médecin de manière sécurisée!")
        print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/reset_doctor_password.py <email>")
        print("Exemple: python scripts/reset_doctor_password.py doctor@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(reset_doctor_password(email))
