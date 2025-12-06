"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Clock } from "lucide-react";
import api from "@/lib/api";
import { TimeSlot } from "@/types";

const DAYS_OF_WEEK = [
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"
];

export default function DoctorSchedulePage() {
    const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);

    const [slotForm, setSlotForm] = useState({
        day_of_week: 0,
        start_time: "09:00",
        end_time: "12:00"
    });

    useEffect(() => {
        fetchSlots();
    }, []);

    const fetchSlots = async () => {
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        setIsLoading(true);
        try {
            const res = await api.get<TimeSlot[]>(`/timeslots?doctor_id=${doctorId}`);
            setTimeSlots(res.data || []);
        } catch (error) {
            console.error("Failed to fetch time slots", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddSlot = async (e: React.FormEvent) => {
        e.preventDefault();
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        try {
            await api.post("/timeslots", {
                doctor_id: doctorId,
                day_of_week: slotForm.day_of_week,
                start_time: slotForm.start_time,
                end_time: slotForm.end_time,
                is_recurring: true
            });
            setShowForm(false);
            setSlotForm({ day_of_week: 0, start_time: "09:00", end_time: "12:00" });
            fetchSlots();
        } catch (error) {
            console.error("Failed to create time slot", error);
            alert("Erreur lors de la création du créneau");
        }
    };

    const handleDeleteSlot = async (slotId: string) => {
        if (!confirm("Supprimer ce créneau ?")) return;
        try {
            await api.delete(`/timeslots/${slotId}`);
            fetchSlots();
        } catch (error) {
            console.error("Failed to delete time slot", error);
        }
    };

    // Group slots by day
    const slotsByDay = DAYS_OF_WEEK.map((day, index) => ({
        day,
        index,
        slots: timeSlots.filter((s) => s.is_recurring && s.day_of_week === index)
    }));

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Mes créneaux</h1>
                    <p className="text-muted-foreground">
                        Définissez vos horaires de disponibilité
                    </p>
                </div>
                <Button onClick={() => setShowForm(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Ajouter un créneau
                </Button>
            </div>

            {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">Chargement...</div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    {slotsByDay.map(({ day, index, slots }) => (
                        <Card key={day} className={slots.length > 0 ? "border-emerald-200 bg-emerald-50/50" : ""}>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Clock className="h-4 w-4" />
                                    {day}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {slots.length === 0 ? (
                                    <p className="text-sm text-muted-foreground">Non disponible</p>
                                ) : (
                                    <div className="space-y-2">
                                        {slots.map((slot) => (
                                            <div
                                                key={slot.slot_id}
                                                className="flex items-center justify-between p-2 bg-white rounded border"
                                            >
                                                <span className="font-mono">
                                                    {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                                                </span>
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
                    ))}
                </div>
            )}

            {/* Add Slot Modal */}
            {showForm && (
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
                                    <Button type="button" variant="outline" className="flex-1" onClick={() => setShowForm(false)}>
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
