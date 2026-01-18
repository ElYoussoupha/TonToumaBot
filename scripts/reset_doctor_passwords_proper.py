#!/usr/bin/env python
"""Reset doctor passwords with proper hashing"""
import asyncio
import sys
import secrets
import hashlib

sys.path.insert(0, r"c:\Users\hp\Documents\Projets\TonToumaBot")

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.doctor import Doctor


def hash_password(password: str) -> str:
    """Hash password using SHA256 + salt"""
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"


async def reset_doctor_passwords():
    """Reset all doctor passwords to 'password123' with proper hashing"""
    async with AsyncSessionLocal() as db:
        # Get all doctors
        stmt = select(Doctor)
        result = await db.execute(stmt)
        doctors = result.scalars().all()
        
        if not doctors:
            print("[Error] No doctors found")
            return
        
        print(f"[OK] Found {len(doctors)} doctors")
        print("-" * 60)
        
        # Reset passwords
        password = "password123"
        hashed_password = hash_password(password)
        
        for doctor in doctors:
            doctor.password_hash = hashed_password
            print(f"[OK] Reset password for Dr. {doctor.first_name} {doctor.last_name}")
        
        await db.commit()
        print("-" * 60)
        print(f"[OK] All passwords reset to '{password}'")
        print("\nCredentials for Dr. Abdoulaye Mbaye:")
        print(f"  Email: abdoulaye.mbaye@hopital-fann.sn")
        print(f"  Password: {password}")


if __name__ == "__main__":
    asyncio.run(reset_doctor_passwords())
