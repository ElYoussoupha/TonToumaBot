"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar, Clock, Users, CheckCircle, AlertCircle, X, Mail, Phone, FileText } from "lucide-react";
import api from "@/lib/api";

interface Appointment {
    appointment_id: string;
    patient_name: string;
    patient_email: string;
    patient_phone?: string;
    date: string;
    start_time: string;
    end_time: string;
    reason: string;
    status: "pending" | "confirmed" | "completed" | "cancelled";
}

interface TimeSlot {
    slot_id: string;
    doctor_id: string;
    day_of_week: number;
    start_time: string;
    end_time: string;
    is_recurring: boolean;
    specific_date: string | null;
}

const DAYS_SHORT = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

export default function DoctorDashboard() {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [doctorName, setDoctorName] = useState("");
    const [consultationDuration] = useState(30);
    const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

    useEffect(() => {
        const name = localStorage.getItem("doctor_name");
        setDoctorName(name || "Médecin");
        fetchData();
    }, []);

    const fetchData = async () => {
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        setIsLoading(true);
        try {
            const [apptRes, slotsRes] = await Promise.all([
                api.get<Appointment[]>(`/appointments?doctor_id=${doctorId}`),
                api.get<TimeSlot[]>(`/timeslots?doctor_id=${doctorId}`)
            ]);
            setAppointments(apptRes.data || []);
            setTimeSlots(slotsRes.data || []);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setIsLoading(false);
        }
    };

    const getNext7Days = () => {
        const days = [];
        const today = new Date();
        for (let i = 0; i < 7; i++) {
            const date = new Date(today);
            date.setDate(today.getDate() + i);
            days.push(date);
        }
        return days;
    };

    const generateTimeGrid = () => {
        const times = [];
        for (let hour = 8; hour < 18; hour++) {
            for (let min = 0; min < 60; min += consultationDuration) {
                times.push(`${hour.toString().padStart(2, "0")}:${min.toString().padStart(2, "0")}`);
            }
        }
        return times;
    };

    const isWithinWorkingHours = (date: Date, time: string) => {
        const jsDay = date.getDay();
        const weekdayIndex = (jsDay + 6) % 7;
        const dateStr = date.toISOString().split("T")[0];

        return timeSlots.some(slot => {
            const matches = slot.is_recurring
                ? slot.day_of_week === weekdayIndex
                : slot.specific_date === dateStr;

            if (!matches) return false;

            const slotStart = slot.start_time.slice(0, 5);
            const slotEnd = slot.end_time.slice(0, 5);
            return time >= slotStart && time < slotEnd;
        });
    };

    const getAppointmentAt = (date: Date, time: string) => {
        const dateStr = date.toISOString().split("T")[0];
        return appointments.find(apt =>
            apt.date === dateStr &&
            apt.start_time.slice(0, 5) === time &&
            apt.status !== "cancelled"
        );
    };

    const todayStr = new Date().toISOString().split("T")[0];
    const todayAppointments = appointments
        .filter(a => a.date === todayStr && a.status !== "cancelled")
        .sort((a, b) => a.start_time.localeCompare(b.start_time));

    const todayTotal = todayAppointments.length;
    const todayCompleted = todayAppointments.filter(a => a.status === "completed").length;
    const todayPending = todayAppointments.filter(a => a.status === "pending" || a.status === "confirmed").length;

    const next7Days = getNext7Days();
    const timeGrid = generateTimeGrid();

    const now = new Date();
    const currentTimeStr = `${now.getHours().toString().padStart(2, "0")}:${Math.floor(now.getMinutes() / consultationDuration) * consultationDuration}`.padEnd(5, "0");

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 rounded-2xl p-6 text-white shadow-xl">
                <h1 className="text-3xl font-bold">
                    Bonjour, Dr. {doctorName.split(" ")[1] || doctorName}
                </h1>
                <p className="text-emerald-100 mt-1">
                    {new Date().toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white border-0 shadow-lg hover:shadow-xl transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-blue-100">RDV aujourd&apos;hui</CardTitle>
                        <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center">
                            <Calendar className="h-5 w-5" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold">{todayTotal}</div>
                        <p className="text-xs text-blue-200 mt-1">patients prévus</p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-green-500 to-emerald-600 text-white border-0 shadow-lg hover:shadow-xl transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-green-100">Terminés</CardTitle>
                        <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center">
                            <CheckCircle className="h-5 w-5" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold">{todayCompleted}</div>
                        <p className="text-xs text-green-200 mt-1">consultations finies</p>
                    </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-amber-500 to-orange-500 text-white border-0 shadow-lg hover:shadow-xl transition-shadow">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-amber-100">En attente</CardTitle>
                        <div className="h-10 w-10 rounded-full bg-white/20 flex items-center justify-center">
                            <AlertCircle className="h-5 w-5" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-4xl font-bold">{todayPending}</div>
                        <p className="text-xs text-amber-200 mt-1">à consulter</p>
                    </CardContent>
                </Card>
            </div>

            {/* Today's Appointments List */}
            <Card className="shadow-xl border-0 overflow-hidden">
                <CardHeader className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
                    <CardTitle className="flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        Rendez-vous du jour
                        {todayTotal > 0 && (
                            <Badge className="bg-white/20 text-white ml-2">{todayTotal}</Badge>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="text-center py-12 text-gray-500">Chargement...</div>
                    ) : todayAppointments.length === 0 ? (
                        <div className="text-center py-12">
                            <Calendar className="h-16 w-16 text-gray-200 mx-auto mb-4" />
                            <p className="text-gray-500 text-lg">Aucun rendez-vous prévu aujourd&apos;hui</p>
                            <p className="text-gray-400 text-sm mt-1">Profitez de votre journée !</p>
                        </div>
                    ) : (
                        <div className="divide-y">
                            {todayAppointments.map((appt, index) => {
                                const isPast = appt.start_time.slice(0, 5) < currentTimeStr;
                                const isCurrent = appt.start_time.slice(0, 5) === currentTimeStr;

                                return (
                                    <div
                                        key={appt.appointment_id}
                                        className={`
                                            flex items-center justify-between p-5 transition-colors cursor-pointer
                                            ${isCurrent ? "bg-emerald-50 border-l-4 border-emerald-500" : ""}
                                            ${isPast && appt.status !== "completed" ? "bg-gray-50" : ""}
                                            ${appt.status === "completed" ? "bg-green-50/50" : ""}
                                            hover:bg-slate-50
                                        `}
                                        onClick={() => setSelectedAppointment(appt)}
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className={`
                                                flex flex-col items-center justify-center w-16 h-16 rounded-xl
                                                ${isCurrent ? "bg-emerald-500 text-white" :
                                                    appt.status === "completed" ? "bg-green-100 text-green-700" :
                                                        "bg-slate-100 text-slate-700"}
                                            `}>
                                                <span className="text-lg font-bold">{appt.start_time.slice(0, 5)}</span>
                                                <span className="text-xs opacity-70">{appt.end_time.slice(0, 5)}</span>
                                            </div>

                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <p className="font-semibold text-gray-900 text-lg">{appt.patient_name}</p>
                                                    {isCurrent && (
                                                        <Badge className="bg-emerald-500 text-white animate-pulse">En cours</Badge>
                                                    )}
                                                </div>
                                                <p className="text-gray-500">{appt.reason}</p>
                                                <p className="text-sm text-gray-400">{appt.patient_email}</p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-3">
                                            <Badge
                                                variant="outline"
                                                className={
                                                    appt.status === "completed" ? "bg-green-100 text-green-800 border-green-300" :
                                                        appt.status === "confirmed" ? "bg-blue-100 text-blue-800 border-blue-300" :
                                                            appt.status === "pending" ? "bg-amber-100 text-amber-800 border-amber-300" :
                                                                "bg-red-100 text-red-800 border-red-300"
                                                }
                                            >
                                                {appt.status === "pending" ? "En attente" :
                                                    appt.status === "confirmed" ? "Confirmé" :
                                                        appt.status === "completed" ? "✓ Terminé" :
                                                            "Annulé"}
                                            </Badge>
                                            <span className="text-2xl font-light text-gray-300">#{index + 1}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Schedule Grid - Next 7 Days */}
            <Card className="shadow-lg border-0">
                <CardHeader className="bg-gradient-to-r from-emerald-700 to-teal-700 text-white rounded-t-lg">
                    <CardTitle className="flex items-center gap-2">
                        <Clock className="h-5 w-5" />
                        Aperçu de la semaine
                    </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                    {isLoading ? (
                        <div className="text-center py-12 text-gray-500">Chargement...</div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full border-collapse">
                                <thead>
                                    <tr className="bg-slate-50">
                                        <th className="p-3 text-left text-sm font-semibold text-gray-600 border-b w-20 sticky left-0 bg-slate-50">Heure</th>
                                        {next7Days.map((date, idx) => (
                                            <th key={idx} className="p-3 text-center text-sm font-semibold text-gray-600 border-b min-w-[120px]">
                                                <div className={`${idx === 0 ? "text-emerald-600" : ""}`}>
                                                    {DAYS_SHORT[date.getDay()]}
                                                </div>
                                                <div className={`text-lg ${idx === 0 ? "text-emerald-600 font-bold" : "text-gray-800"}`}>
                                                    {date.getDate()}/{(date.getMonth() + 1).toString().padStart(2, "0")}
                                                </div>
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {timeGrid.map((time, timeIdx) => (
                                        <tr key={time} className={timeIdx % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
                                            <td className="p-2 text-sm font-mono text-gray-600 border-r sticky left-0 bg-inherit">
                                                {time}
                                            </td>
                                            {next7Days.map((date, dayIdx) => {
                                                const appointment = getAppointmentAt(date, time);
                                                const isWorking = isWithinWorkingHours(date, time);

                                                if (!isWorking) {
                                                    return (
                                                        <td key={dayIdx} className="p-1 border text-center bg-gray-100">
                                                            <div className="h-10 flex items-center justify-center text-gray-300 text-xs">
                                                                —
                                                            </div>
                                                        </td>
                                                    );
                                                }

                                                if (appointment) {
                                                    return (
                                                        <td key={dayIdx} className="p-1 border">
                                                            <div
                                                                onClick={() => setSelectedAppointment(appointment)}
                                                                className="h-10 flex items-center justify-center bg-gradient-to-r from-blue-100 to-indigo-100 rounded-md px-2 hover:from-blue-200 hover:to-indigo-200 transition-colors cursor-pointer shadow-sm"
                                                            >
                                                                <span className="text-xs font-medium text-blue-800 truncate">
                                                                    {appointment.patient_name.split(" ")[0]}
                                                                </span>
                                                            </div>
                                                        </td>
                                                    );
                                                }

                                                return (
                                                    <td key={dayIdx} className="p-1 border">
                                                        <div className="h-10 flex items-center justify-center bg-green-50 rounded-md text-green-600 text-xs hover:bg-green-100 transition-colors cursor-pointer">
                                                            Libre
                                                        </div>
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Appointment Detail Modal */}
            {selectedAppointment && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedAppointment(null)}>
                    <Card className="w-full max-w-md mx-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
                        <CardHeader className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-t-lg">
                            <div className="flex items-center justify-between">
                                <CardTitle className="flex items-center gap-2">
                                    <Users className="h-5 w-5" />
                                    Détails du rendez-vous
                                </CardTitle>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={() => setSelectedAppointment(null)}
                                    className="text-white hover:bg-white/20"
                                >
                                    <X className="h-5 w-5" />
                                </Button>
                            </div>
                        </CardHeader>
                        <CardContent className="p-6 space-y-4">
                            {/* Date & Time */}
                            <div className="flex items-center justify-between bg-slate-50 rounded-xl p-4">
                                <div className="flex items-center gap-3">
                                    <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center">
                                        <Calendar className="h-6 w-6 text-emerald-600" />
                                    </div>
                                    <div>
                                        <p className="font-semibold text-gray-900">
                                            {new Date(selectedAppointment.date + "T00:00:00").toLocaleDateString("fr-FR", {
                                                weekday: "long",
                                                day: "numeric",
                                                month: "long"
                                            })}
                                        </p>
                                        <p className="text-emerald-600 font-mono font-bold">
                                            {selectedAppointment.start_time.slice(0, 5)} - {selectedAppointment.end_time.slice(0, 5)}
                                        </p>
                                    </div>
                                </div>
                                <Badge className={
                                    selectedAppointment.status === "completed" ? "bg-green-100 text-green-800" :
                                        selectedAppointment.status === "confirmed" ? "bg-blue-100 text-blue-800" :
                                            selectedAppointment.status === "pending" ? "bg-amber-100 text-amber-800" :
                                                "bg-red-100 text-red-800"
                                }>
                                    {selectedAppointment.status === "pending" ? "En attente" :
                                        selectedAppointment.status === "confirmed" ? "Confirmé" :
                                            selectedAppointment.status === "completed" ? "Terminé" : "Annulé"}
                                </Badge>
                            </div>

                            {/* Patient Info */}
                            <div className="space-y-3">
                                <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wider">Patient</h4>
                                <div className="space-y-2">
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                        <Users className="h-5 w-5 text-gray-400" />
                                        <span className="font-medium text-gray-900">{selectedAppointment.patient_name}</span>
                                    </div>
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                        <Mail className="h-5 w-5 text-gray-400" />
                                        <span className="text-gray-600">{selectedAppointment.patient_email}</span>
                                    </div>
                                    {selectedAppointment.patient_phone && (
                                        <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                            <Phone className="h-5 w-5 text-gray-400" />
                                            <span className="text-gray-600">{selectedAppointment.patient_phone}</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Reason */}
                            <div className="space-y-2">
                                <h4 className="font-semibold text-gray-700 text-sm uppercase tracking-wider">Motif</h4>
                                <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg">
                                    <FileText className="h-5 w-5 text-amber-500 mt-0.5" />
                                    <span className="text-gray-700">{selectedAppointment.reason}</span>
                                </div>
                            </div>

                            {/* Action Button */}
                            <Button
                                className="w-full bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => setSelectedAppointment(null)}
                            >
                                Fermer
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
