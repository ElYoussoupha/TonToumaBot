import asyncio
import random
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, time, date

import sys
import os
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal as SessionLocal
from app.models.entity import Entity
from app.models.doctor import Doctor
from app.models.specialty import Specialty
from app.models.timeslot import TimeSlot
from app.models.appointment import Appointment, AppointmentStatus

# Proper password hash to match app authentication
def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

# Data
SPECIALTIES_DATA = [
    "Cardiologie", "Neurologie", "Pédiatrie", "Orthopédie", "Dermatologie",
    "Gynécologie", "Ophtalmologie", "Psychiatrie", "ORL", "Urologie"
]

DOCTOR_NAMES = [
    ("Amadou", "Diallo"), ("Fatou", "Sow"), ("Moussa", "Ndiaye"), ("Awa", "Diop"),
    ("Cheikh", "Fall"), ("Mariama", "Ba"), ("Oumar", "Ly"), ("Aminata", "Gueye"),
    ("Ibrahima", "Konaté"), ("Seynabou", "Thiam"), ("Abdoulaye", "Mbaye"), ("Khady", "Cisse")
]

PATIENT_NAMES = [
    ("Mamadou", "Diop"), ("Aissatou", "Fall"), ("Babacar", "Ndiaye"), ("Khady", "Sow"),
    ("Ousmane", "Diallo"), ("Aminata", "Faye"), ("Cheikh", "Gueye"), ("Fatou", "Ba"),
    ("Ibrahima", "Seck"), ("Marieme", "Sy"), ("Abdoulaye", "Wade"), ("Sokhna", "Dieng"),
    ("Samba", "Ka"), ("Ndeye", "Fall"), ("Malick", "Gaye"), ("Astou", "Samb")
]

REASONS = [
    "Consultation de routine", "Douleurs persistantes", "Suivi traitement",
    "Renouvellement ordonnance", "Check-up annuel", "Avis médical"
]

async def seed_doctors_and_appointments():
    async with SessionLocal() as db:
        print("[Search] Recherche de l'entité 'Hôpital Fann'...")
        stmt = select(Entity).where(Entity.name.ilike("%Fann%"))
        result = await db.execute(stmt)
        entity = result.scalars().first()
        if not entity:
            print("[Error] Entité 'Hôpital Fann' introuvable.")
            return

        # 1. Create Specialties
        print("[Info] Création des spécialités...")
        created_specialties = []
        for spec_name in SPECIALTIES_DATA:
            stmt = select(Specialty).where(Specialty.name == spec_name)
            res = await db.execute(stmt)
            existing = res.scalars().first()
            if not existing:
                spec = Specialty(name=spec_name, description=f"Spécialité médicale : {spec_name}")
                db.add(spec)
                await db.flush()  # get ID
                created_specialties.append(spec)
            else:
                created_specialties.append(existing)
        await db.commit()

        # 2. Create Doctors
        print("[Info] Création des médecins...")
        doctors = []
        for first, last in DOCTOR_NAMES:
            email = f"{first.lower()}.{last.lower()}@hopital-fann.sn"
            stmt = select(Doctor).where(Doctor.email == email)
            res = await db.execute(stmt)
            doc = res.scalars().first()
            if not doc:
                specialty = random.choice(created_specialties)
                doc = Doctor(
                    entity_id=entity.entity_id,
                    specialty_id=specialty.specialty_id,
                    first_name=first,
                    last_name=last,
                    email=email,
                    password_hash=get_password_hash("password123"),
                    phone=f"+22177{random.randint(1000000, 9999999)}",
                    consultation_duration=30,
                    is_active=True
                )
                db.add(doc)
                await db.flush()
                print(f"   + Dr. {first} {last} ({specialty.name})")
            doctors.append(doc)

        # Reload all doctors for this entity
        stmt = select(Doctor).where(Doctor.entity_id == entity.entity_id)
        res = await db.execute(stmt)
        doctors = res.scalars().all()
        await db.commit()

        # 3. CLEANUP - Remove all existing TimeSlots and Appointments
        print("[Clean] Nettoyage des anciens créneaux et rendez-vous...")
        doctor_ids = [d.doctor_id for d in doctors]
        if doctor_ids:
            await db.execute(delete(Appointment).where(Appointment.doctor_id.in_(doctor_ids)))
            await db.execute(delete(TimeSlot).where(TimeSlot.doctor_id.in_(doctor_ids)))
            await db.commit()
            print("   [Clean] Données effacées pour recréation propre.")

        # 4. Create TimeSlots (Availability) - Specific Dates for next 14 days
        print("[Info] Génération des nouveaux créneaux (Dates exactes)...")
        start_date = date.today()
        days_ahead = 14
        for doc in doctors:
            for day_offset in range(days_ahead):
                current_date = start_date + timedelta(days=day_offset)
                if current_date.weekday() == 6:  # Skip Sundays
                    continue
                if random.random() > 0.7:
                    continue
                shifts = []
                rand_val = random.random()
                if rand_val < 0.4:
                    shifts.append((9, 12))
                elif rand_val < 0.8:
                    shifts.append((14, 18))
                else:
                    shifts.append((9, 13))
                for start_h, end_h in shifts:
                    slot = TimeSlot(
                        doctor_id=doc.doctor_id,
                        specific_date=current_date,
                        start_time=time(start_h, 0),
                        end_time=time(end_h, 0),
                        is_recurring=False,
                        is_active=True
                    )
                    db.add(slot)
        await db.commit()

        # 5. Create Appointments (Fill ~40% of capacity)
        print("[Info] Simulation de prise de rendez-vous...")
        stmt = select(TimeSlot).where(TimeSlot.doctor_id.in_(doctor_ids))
        res = await db.execute(stmt)
        all_slots = res.scalars().all()
        appointments_created = 0
        for slot in all_slots:
            if random.random() < 0.3:
                continue
            slot_start_dt = datetime.combine(slot.specific_date, slot.start_time)
            slot_end_dt = datetime.combine(slot.specific_date, slot.end_time)
            duration_mins = (datetime.combine(date.min, slot.end_time) - datetime.combine(date.min, slot.start_time)).total_seconds() / 60
            max_appts = int(duration_mins / 30)
            num_to_book = random.randint(1, max(1, max_appts))
            current_dt = slot_start_dt
            booked_count = 0
            while current_dt + timedelta(minutes=30) <= slot_end_dt and booked_count < num_to_book:
                if random.random() < 0.3:
                    current_dt += timedelta(minutes=30)
                    continue
                pat_first, pat_last = random.choice(PATIENT_NAMES)
                status = AppointmentStatus.CONFIRMED
                if current_dt < datetime.now():
                    status = AppointmentStatus.COMPLETED
                appt = Appointment(
                    doctor_id=slot.doctor_id,
                    patient_name=f"{pat_first} {pat_last}",
                    patient_email=f"{pat_first.lower()}.{pat_last.lower()}@gmail.com",
                    patient_phone="770000000",
                    reason=random.choice(REASONS),
                    date=current_dt.date(),
                    start_time=current_dt.time(),
                    end_time=(current_dt + timedelta(minutes=30)).time(),
                    status=status
                )
                db.add(appt)
                appointments_created += 1
                booked_count += 1
                current_dt += timedelta(minutes=30)
        await db.commit()
        print(f"[Success] {appointments_created} rendez-vous créés sur {len(all_slots)} créneaux.")
        print("[Done] Base de données régénérée avec succès !")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed_doctors_and_appointments())