"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Plus, Trash2, Clock, Calendar, Settings } from "lucide-react";
import api from "@/lib/api";

interface TimeSlot {
    slot_id: string;
    doctor_id: string;
    day_of_week: number;
    start_time: string;
    end_time: string;
    is_recurring: boolean;
    specific_date: string | null;
}

const DAYS_OF_WEEK = [
    "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"
];

export default function MesCreneauxPage() {
    const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [consultationDuration, setConsultationDuration] = useState(30);
    const [formMode, setFormMode] = useState<"recurring" | "specific">("recurring");

    const [slotForm, setSlotForm] = useState({
        day_of_week: 0,
        specific_date: "",
        start_time: "09:00",
        end_time: "12:00"
    });

    useEffect(() => {
        fetchData();
        // Load saved consultation duration
        const savedDuration = localStorage.getItem("consultation_duration");
        if (savedDuration) {
            setConsultationDuration(parseInt(savedDuration));
        }
    }, []);

    const fetchData = async () => {
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        setIsLoading(true);
        try {
            const response = await api.get<TimeSlot[]>(`/timeslots?doctor_id=${doctorId}`);
            setTimeSlots(response.data || []);
        } catch (error) {
            console.error("Failed to fetch time slots", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveDuration = () => {
        localStorage.setItem("consultation_duration", consultationDuration.toString());
        alert(`Durée de consultation sauvegardée: ${consultationDuration} minutes`);
    };

    const handleAddSlot = async (e: React.FormEvent) => {
        e.preventDefault();
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        try {
            const payload = formMode === "recurring"
                ? {
                    doctor_id: doctorId,
                    day_of_week: slotForm.day_of_week,
                    start_time: slotForm.start_time,
                    end_time: slotForm.end_time,
                    is_recurring: true
                }
                : {
                    doctor_id: doctorId,
                    specific_date: slotForm.specific_date,
                    start_time: slotForm.start_time,
                    end_time: slotForm.end_time,
                    is_recurring: false
                };

            await api.post("/timeslots", payload);
            setShowForm(false);
            setSlotForm({ day_of_week: 0, specific_date: "", start_time: "09:00", end_time: "12:00" });
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

    // Group slots by recurring vs specific
    const recurringSlots = timeSlots.filter(s => s.is_recurring);
    const specificSlots = timeSlots.filter(s => !s.is_recurring);

    // Group recurring by day
    const slotsByDay = DAYS_OF_WEEK.map((day, index) => ({
        day,
        index,
        slots: recurringSlots.filter(s => s.day_of_week === index)
    }));

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Mes créneaux</h1>
                    <p className="text-gray-500">
                        Configurez vos disponibilités et la durée de consultation
                    </p>
                </div>
                <Button onClick={() => setShowForm(true)} className="bg-emerald-600 hover:bg-emerald-700">
                    <Plus className="mr-2 h-4 w-4" />
                    Ajouter un créneau
                </Button>
            </div>

            {/* Consultation Duration Setting */}
            <Card className="border-0 shadow-md bg-gradient-to-r from-slate-50 to-white">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <Settings className="h-5 w-5 text-emerald-600" />
                        Durée de consultation
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Label>Durée moyenne :</Label>
                            <select
                                className="rounded-md border border-gray-300 px-3 py-2 bg-white"
                                value={consultationDuration}
                                onChange={(e) => setConsultationDuration(parseInt(e.target.value))}
                            >
                                <option value={15}>15 minutes</option>
                                <option value={20}>20 minutes</option>
                                <option value={30}>30 minutes</option>
                                <option value={45}>45 minutes</option>
                                <option value={60}>60 minutes</option>
                            </select>
                        </div>
                        <Button onClick={handleSaveDuration} variant="outline" size="sm">
                            Sauvegarder
                        </Button>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">
                        Cette durée sera utilisée pour diviser vos créneaux en rendez-vous individuels.
                    </p>
                </CardContent>
            </Card>

            {isLoading ? (
                <div className="text-center py-12 text-gray-500">Chargement...</div>
            ) : (
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Recurring Slots */}
                    <Card className="border-0 shadow-md">
                        <CardHeader className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg">
                            <CardTitle className="flex items-center gap-2">
                                <Clock className="h-5 w-5" />
                                Créneaux récurrents
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4">
                            {recurringSlots.length === 0 ? (
                                <p className="text-center text-gray-500 py-8">
                                    Aucun créneau récurrent configuré
                                </p>
                            ) : (
                                <div className="space-y-4">
                                    {slotsByDay.filter(d => d.slots.length > 0).map(({ day, slots }) => (
                                        <div key={day} className="border-b pb-3 last:border-0">
                                            <h4 className="font-semibold text-gray-800 mb-2">{day}</h4>
                                            <div className="space-y-2">
                                                {slots.map(slot => (
                                                    <div
                                                        key={slot.slot_id}
                                                        className="flex items-center justify-between bg-blue-50 rounded-lg p-3"
                                                    >
                                                        <div className="flex items-center gap-3">
                                                            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                                                                <Clock className="h-4 w-4 text-blue-600" />
                                                            </div>
                                                            <span className="font-mono text-sm">
                                                                {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                                                            </span>
                                                        </div>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            onClick={() => handleDeleteSlot(slot.slot_id)}
                                                            className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Specific Date Slots */}
                    <Card className="border-0 shadow-md">
                        <CardHeader className="bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-t-lg">
                            <CardTitle className="flex items-center gap-2">
                                <Calendar className="h-5 w-5" />
                                Créneaux pour dates spécifiques
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4">
                            {specificSlots.length === 0 ? (
                                <p className="text-center text-gray-500 py-8">
                                    Aucun créneau spécifique configuré
                                </p>
                            ) : (
                                <div className="space-y-2">
                                    {specificSlots
                                        .sort((a, b) => (a.specific_date || "").localeCompare(b.specific_date || ""))
                                        .map(slot => (
                                            <div
                                                key={slot.slot_id}
                                                className="flex items-center justify-between bg-amber-50 rounded-lg p-3"
                                            >
                                                <div className="flex items-center gap-3">
                                                    <div className="h-8 w-8 rounded-full bg-amber-100 flex items-center justify-center">
                                                        <Calendar className="h-4 w-4 text-amber-600" />
                                                    </div>
                                                    <div>
                                                        <div className="font-medium text-sm">
                                                            {new Date(slot.specific_date + "T00:00:00").toLocaleDateString("fr-FR", {
                                                                weekday: "short",
                                                                day: "numeric",
                                                                month: "short"
                                                            })}
                                                        </div>
                                                        <div className="font-mono text-xs text-gray-600">
                                                            {slot.start_time.slice(0, 5)} - {slot.end_time.slice(0, 5)}
                                                        </div>
                                                    </div>
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() => handleDeleteSlot(slot.slot_id)}
                                                    className="text-red-500 hover:text-red-700 hover:bg-red-50"
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </div>
                                        ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Add Slot Modal */}
            {showForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-md mx-4 shadow-2xl">
                        <CardHeader className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-t-lg">
                            <CardTitle>Ajouter un créneau</CardTitle>
                        </CardHeader>
                        <CardContent className="pt-6">
                            {/* Mode Toggle */}
                            <div className="flex gap-2 mb-6">
                                <Button
                                    type="button"
                                    variant={formMode === "recurring" ? "default" : "outline"}
                                    onClick={() => setFormMode("recurring")}
                                    className={formMode === "recurring" ? "bg-blue-600" : ""}
                                >
                                    Récurrent
                                </Button>
                                <Button
                                    type="button"
                                    variant={formMode === "specific" ? "default" : "outline"}
                                    onClick={() => setFormMode("specific")}
                                    className={formMode === "specific" ? "bg-amber-600" : ""}
                                >
                                    Date spécifique
                                </Button>
                            </div>

                            <form onSubmit={handleAddSlot} className="space-y-4">
                                {formMode === "recurring" ? (
                                    <div className="space-y-2">
                                        <Label>Jour de la semaine</Label>
                                        <select
                                            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2"
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
                                ) : (
                                    <div className="space-y-2">
                                        <Label>Date</Label>
                                        <Input
                                            type="date"
                                            value={slotForm.specific_date}
                                            onChange={(e) => setSlotForm({ ...slotForm, specific_date: e.target.value })}
                                            required
                                        />
                                    </div>
                                )}

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
                                    <Button
                                        type="button"
                                        variant="outline"
                                        className="flex-1"
                                        onClick={() => setShowForm(false)}
                                    >
                                        Annuler
                                    </Button>
                                    <Button
                                        type="submit"
                                        className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                                    >
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
