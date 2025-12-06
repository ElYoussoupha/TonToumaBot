from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.specialty import Specialty
from app.models.doctor import Doctor
from app.models.timeslot import TimeSlot
from app.models.appointment import Appointment
from app.schemas.specialty import SpecialtyCreate, SpecialtyUpdate
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate


class CRUDSpecialty(CRUDBase[Specialty, SpecialtyCreate, SpecialtyUpdate]):
    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[Specialty]:
        result = await db.execute(select(Specialty).filter(Specialty.name.ilike(name)))
        return result.scalars().first()


class CRUDDoctor(CRUDBase[Doctor, DoctorCreate, DoctorUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Doctor]:
        result = await db.execute(select(Doctor).filter(Doctor.email == email))
        return result.scalars().first()

    async def get_by_entity_id(self, db: AsyncSession, *, entity_id: UUID) -> List[Doctor]:
        result = await db.execute(
            select(Doctor).filter(Doctor.entity_id == entity_id, Doctor.is_active == True)
        )
        return result.scalars().all()

    async def get_by_specialty(self, db: AsyncSession, *, entity_id: UUID, specialty_id: UUID) -> List[Doctor]:
        result = await db.execute(
            select(Doctor).filter(
                Doctor.entity_id == entity_id,
                Doctor.specialty_id == specialty_id,
                Doctor.is_active == True
            )
        )
        return result.scalars().all()


class CRUDTimeSlot(CRUDBase[TimeSlot, TimeSlotCreate, TimeSlotUpdate]):
    async def get_by_doctor_id(self, db: AsyncSession, *, doctor_id: UUID) -> List[TimeSlot]:
        result = await db.execute(
            select(TimeSlot).filter(TimeSlot.doctor_id == doctor_id, TimeSlot.is_active == True)
        )
        return result.scalars().all()


class CRUDAppointment(CRUDBase[Appointment, AppointmentCreate, AppointmentUpdate]):
    async def get_by_doctor_id(self, db: AsyncSession, *, doctor_id: UUID) -> List[Appointment]:
        result = await db.execute(
            select(Appointment).filter(Appointment.doctor_id == doctor_id)
        )
        return result.scalars().all()

    async def get_by_doctor_and_date(self, db: AsyncSession, *, doctor_id: UUID, date) -> List[Appointment]:
        from app.models.appointment import AppointmentStatus
        result = await db.execute(
            select(Appointment).filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date == date,
                Appointment.status != AppointmentStatus.CANCELLED
            )
        )
        return result.scalars().all()

    async def get_by_session_id(self, db: AsyncSession, *, session_id: UUID) -> List[Appointment]:
        result = await db.execute(
            select(Appointment).filter(Appointment.session_id == session_id)
        )
        return result.scalars().all()


# Singleton instances
specialty = CRUDSpecialty(Specialty)
doctor = CRUDDoctor(Doctor)
time_slot = CRUDTimeSlot(TimeSlot)
appointment = CRUDAppointment(Appointment)
