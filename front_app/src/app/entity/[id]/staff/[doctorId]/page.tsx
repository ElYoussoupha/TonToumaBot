"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Plus, Trash2, Calendar, Clock } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { Doctor, TimeSlot, Appointment } from "@/types";

const DAYS_OF_WEEK = [
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"
];

export default function DoctorSchedulePage() {
    const params = useParams();
    const entityId = params.id as string;
    const doctorId = params.doctorId as string;

    const [doctor, setDoctor] = useState<Doctor | null>(null);
    const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showSlotForm, setShowSlotForm] = useState(false);

    // Form state
    const [slotForm, setSlotForm] = useState({
        day_of_week: 0,
        start_time: "09:00",
        end_time: "12:00",
        is_recurring: true
    });

    useEffect(() => {
        fetchData();
    }, [doctorId]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [doctorRes, slotsRes, apptRes] = await Promise.all([
                api.get<Doctor>(`/doctors/${doctorId}`),
                api.get<TimeSlot[]>(`/timeslots?doctor_id=${doctorId}`),
                api.get<Appointment[]>(`/appointments?doctor_id=${doctorId}`)
            ]);
            setDoctor(doctorRes.data);
            setTimeSlots(slotsRes.data || []);
            setAppointments(apptRes.data || []);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddSlot = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await api.post("/timeslots", {
                doctor_id: doctorId,
                day_of_week: slotForm.day_of_week,
                start_time: slotForm.start_time,
                end_time: slotForm.end_time,
                is_recurring: true
            });
            setShowSlotForm(false);
            fetchData();
        } catch (error) {
            console.error("Failed to create time slot", error);
            alert("Erreur lors de la création du créneau");
        }
    };

    const handleDeleteSlot = async (slotId: string) => {
        if (!confirm("Supprimer ce créneau ?")) return;
        try {
            await api.delete(`/timeslots/${slotId}`);
            fetchData();
        } catch (error) {
            console.error("Failed to delete time slot", error);
        }
    };

    if (isLoading) {
        return <div className="text-center py-8">Chargement...</div>;
    }

    if (!doctor) {
        return <div className="text-center py-8 text-red-500">Médecin non trouvé</div>;
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <Link href={`/entity/${entityId}/staff`}>
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">
                        Dr. {doctor.first_name} {doctor.last_name}
                    </h1>
                    {doctor.specialty_name && (
                        <p className="text-muted-foreground">{doctor.specialty_name}</p>
                    )}
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Time Slots */}
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between">
                        <CardTitle className="flex items-center gap-2">
                            <Clock className="h-5 w-5" />
                            Créneaux horaires
                        </CardTitle>
                        <Button size="sm" onClick={() => setShowSlotForm(true)}>
                            <Plus className="mr-2 h-4 w-4" />
                            Ajouter
                        </Button>
                    </CardHeader>
                    <CardContent>
                        {timeSlots.length === 0 ? (
                            <p className="text-center text-muted-foreground py-4">
                                Aucun créneau défini
                            </p>
                        ) : (
                            <div className="space-y-2">
                                {timeSlots.map((slot) => (
                                    <div
                                        key={slot.slot_id}
                                        className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                                    >
                                        <div>
                                            <span className="font-medium">
                                                {slot.is_recurring && slot.day_of_week !== undefined
                                                    ? DAYS_OF_WEEK[slot.day_of_week]
                                                    : slot.specific_date}
                                            </span>
                                            <span className="text-muted-foreground ml-2">
                                                {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                                            </span>
                                        </div>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => handleDeleteSlot(slot.slot_id)}
                                        >
                                            <Trash2 className="h-4 w-4 text-red-500" />
                                        </Button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Upcoming Appointments */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="h-5 w-5" />
                            Prochains rendez-vous
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        {appointments.length === 0 ? (
                            <p className="text-center text-muted-foreground py-4">
                                Aucun rendez-vous prévu
                            </p>
                        ) : (
                            <div className="space-y-2">
                                {appointments.slice(0, 10).map((appt) => (
                                    <div
                                        key={appt.appointment_id}
                                        className="p-3 bg-slate-50 rounded-lg"
                                    >
                                        <div className="flex items-center justify-between">
                                            <span className="font-medium">{appt.patient_name}</span>
                                            <Badge variant={
                                                appt.status === "confirmed" ? "default" :
                                                    appt.status === "cancelled" ? "destructive" :
                                                        "secondary"
                                            }>
                                                {appt.status}
                                            </Badge>
                                        </div>
                                        <div className="text-sm text-muted-foreground">
                                            {appt.date} à {appt.start_time.slice(0, 5)}
                                        </div>
                                        <div className="text-sm text-muted-foreground truncate">
                                            {appt.reason}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Add Slot Modal */}
            {showSlotForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-md mx-4">
                        <CardHeader>
                            <CardTitle>Ajouter un créneau</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleAddSlot} className="space-y-4">
                                <div className="space-y-2">
                                    <Label>Jour de la semaine</Label>
                                    <select
                                        className="w-full rounded-md border border-input bg-background px-3 py-2"
                                        value={slotForm.day_of_week}
                                        onChange={(e) => setSlotForm({ ...slotForm, day_of_week: parseInt(e.target.value) })}
                                    >
                                        {DAYS_OF_WEEK.map((day, index) => (
                                            <option key={index} value={index}>
                                                {day}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Heure début</Label>
                                        <Input
                                            type="time"
                                            value={slotForm.start_time}
                                            onChange={(e) => setSlotForm({ ...slotForm, start_time: e.target.value })}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Heure fin</Label>
                                        <Input
                                            type="time"
                                            value={slotForm.end_time}
                                            onChange={(e) => setSlotForm({ ...slotForm, end_time: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div className="flex gap-2 pt-4">
                                    <Button type="button" variant="outline" className="flex-1" onClick={() => setShowSlotForm(false)}>
                                        Annuler
                                    </Button>
                                    <Button type="submit" className="flex-1">
                                        Créer
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
