"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChevronLeft, ChevronRight, Calendar, Clock, User, Mail, Phone, FileText } from "lucide-react";
import api from "@/lib/api";

interface Appointment {
    appointment_id: string;
    patient_name: string;
    patient_email: string;
    patient_phone: string;
    date: string;
    start_time: string;
    end_time: string;
    reason: string;
    status: "pending" | "confirmed" | "completed" | "cancelled";
}

const MONTH_NAMES = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
];

const DAY_NAMES = ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"];

export default function MonCalendrierPage() {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [currentDate, setCurrentDate] = useState(new Date());
    const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const doctorId = localStorage.getItem("doctor_id");
        if (!doctorId) return;

        setIsLoading(true);
        try {
            const response = await api.get<Appointment[]>(`/appointments?doctor_id=${doctorId}`);
            setAppointments(response.data || []);
        } catch (error) {
            console.error("Failed to fetch appointments", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleStatusChange = async (appointmentId: string, newStatus: string) => {
        try {
            await api.put(`/appointments/${appointmentId}`, { status: newStatus });
            fetchData();
        } catch (error) {
            console.error("Failed to update status", error);
        }
    };

    // Calendar helpers
    const getDaysInMonth = (date: Date) => {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    };

    const getFirstDayOfMonth = (date: Date) => {
        return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    };

    const getAppointmentsForDate = (date: Date) => {
        const dateStr = date.toISOString().split("T")[0];
        return appointments.filter(apt => apt.date === dateStr && apt.status !== "cancelled");
    };

    const previousMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
    };

    const nextMonth = () => {
        setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
    };

    // Calendar grid
    const calendarDays: (Date | null)[] = [];
    const firstDay = getFirstDayOfMonth(currentDate);
    const daysInMonth = getDaysInMonth(currentDate);

    for (let i = 0; i < firstDay; i++) {
        calendarDays.push(null);
    }
    for (let i = 1; i <= daysInMonth; i++) {
        calendarDays.push(new Date(currentDate.getFullYear(), currentDate.getMonth(), i));
    }

    // Selected date appointments
    const selectedAppointments = selectedDate
        ? getAppointmentsForDate(selectedDate).sort((a, b) => a.start_time.localeCompare(b.start_time))
        : [];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Mon calendrier</h1>
                <p className="text-gray-500">
                    Consultez vos rendez-vous jour par jour
                </p>
            </div>

            {isLoading ? (
                <div className="text-center py-12 text-gray-500">Chargement...</div>
            ) : (
                <div className="grid gap-6 lg:grid-cols-3">
                    {/* Calendar */}
                    <div className="lg:col-span-2">
                        <Card className="shadow-lg border-0 overflow-hidden">
                            <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white pb-4">
                                <div className="flex items-center justify-between">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={previousMonth}
                                        className="text-white hover:bg-white/20"
                                    >
                                        <ChevronLeft className="h-5 w-5" />
                                    </Button>
                                    <h2 className="text-xl font-semibold">
                                        {MONTH_NAMES[currentDate.getMonth()]} {currentDate.getFullYear()}
                                    </h2>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={nextMonth}
                                        className="text-white hover:bg-white/20"
                                    >
                                        <ChevronRight className="h-5 w-5" />
                                    </Button>
                                </div>
                            </CardHeader>
                            <CardContent className="p-4">
                                {/* Days header */}
                                <div className="grid grid-cols-7 gap-2 mb-2">
                                    {DAY_NAMES.map(day => (
                                        <div key={day} className="text-center font-semibold text-sm text-gray-500 py-2">
                                            {day}
                                        </div>
                                    ))}
                                </div>
                                {/* Calendar grid */}
                                <div className="grid grid-cols-7 gap-2">
                                    {calendarDays.map((date, index) => {
                                        const appts = date ? getAppointmentsForDate(date) : [];
                                        const isToday = date && new Date().toDateString() === date.toDateString();
                                        const isSelected = date && selectedDate && date.toDateString() === selectedDate.toDateString();
                                        const isPast = date && date < new Date(new Date().setHours(0, 0, 0, 0));

                                        return (
                                            <div
                                                key={index}
                                                onClick={() => date && setSelectedDate(date)}
                                                className={`
                                                    min-h-[80px] p-2 rounded-lg border cursor-pointer transition-all
                                                    ${!date ? "bg-gray-50 opacity-30 cursor-default" : ""}
                                                    ${isToday ? "border-indigo-500 bg-indigo-50" : "border-gray-200"}
                                                    ${isSelected ? "bg-indigo-100 border-indigo-600 ring-2 ring-indigo-300" : "hover:bg-gray-50"}
                                                    ${isPast && !isToday ? "opacity-60" : ""}
                                                `}
                                            >
                                                {date && (
                                                    <div className="h-full flex flex-col">
                                                        <span className={`text-sm font-semibold ${isToday ? "text-indigo-600" : "text-gray-700"}`}>
                                                            {date.getDate()}
                                                        </span>
                                                        {appts.length > 0 && (
                                                            <div className="flex-1 flex items-end mt-1">
                                                                <div className={`
                                                                    text-xs px-1.5 py-0.5 rounded-full font-medium
                                                                    ${appts.length >= 3 ? "bg-red-100 text-red-700" :
                                                                        appts.length >= 1 ? "bg-amber-100 text-amber-700" :
                                                                            "bg-gray-100 text-gray-600"}
                                                                `}>
                                                                    {appts.length} RDV
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    {/* Selected Date Details */}
                    <div>
                        <Card className="shadow-lg border-0 sticky top-4">
                            <CardHeader className="bg-gradient-to-r from-slate-700 to-slate-800 text-white rounded-t-lg">
                                <CardTitle className="flex items-center gap-2 text-lg">
                                    <Calendar className="h-5 w-5" />
                                    {selectedDate
                                        ? selectedDate.toLocaleDateString("fr-FR", {
                                            weekday: "long",
                                            day: "numeric",
                                            month: "long"
                                        })
                                        : "Sélectionnez une date"
                                    }
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="p-4">
                                {!selectedDate ? (
                                    <p className="text-center text-gray-500 py-8">
                                        Cliquez sur une date pour voir les détails
                                    </p>
                                ) : selectedAppointments.length === 0 ? (
                                    <div className="text-center py-8">
                                        <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                                        <p className="text-gray-500">Aucun rendez-vous ce jour</p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {selectedAppointments.map(apt => (
                                            <div
                                                key={apt.appointment_id}
                                                className="p-4 bg-gradient-to-r from-slate-50 to-white rounded-xl border hover:shadow-md transition-shadow"
                                            >
                                                {/* Time & Status */}
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        <Clock className="h-4 w-4 text-indigo-600" />
                                                        <span className="font-mono font-semibold text-indigo-600">
                                                            {apt.start_time.slice(0, 5)} - {apt.end_time.slice(0, 5)}
                                                        </span>
                                                    </div>
                                                    <Badge className={
                                                        apt.status === "completed" ? "bg-green-100 text-green-800" :
                                                            apt.status === "confirmed" ? "bg-blue-100 text-blue-800" :
                                                                apt.status === "pending" ? "bg-yellow-100 text-yellow-800" :
                                                                    "bg-red-100 text-red-800"
                                                    }>
                                                        {apt.status === "pending" ? "En attente" :
                                                            apt.status === "confirmed" ? "Confirmé" :
                                                                apt.status === "completed" ? "Terminé" : "Annulé"}
                                                    </Badge>
                                                </div>

                                                {/* Patient Info */}
                                                <div className="space-y-2">
                                                    <div className="flex items-center gap-2">
                                                        <User className="h-4 w-4 text-gray-400" />
                                                        <span className="font-semibold text-gray-900">{apt.patient_name}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Mail className="h-4 w-4 text-gray-400" />
                                                        <span className="text-sm text-gray-600">{apt.patient_email}</span>
                                                    </div>
                                                    {apt.patient_phone && (
                                                        <div className="flex items-center gap-2">
                                                            <Phone className="h-4 w-4 text-gray-400" />
                                                            <span className="text-sm text-gray-600">{apt.patient_phone}</span>
                                                        </div>
                                                    )}
                                                    <div className="flex items-start gap-2">
                                                        <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
                                                        <span className="text-sm text-gray-600">{apt.reason}</span>
                                                    </div>
                                                </div>

                                                {/* Actions */}
                                                {apt.status !== "completed" && apt.status !== "cancelled" && (
                                                    <div className="flex gap-2 mt-4 pt-3 border-t">
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            className="flex-1 text-green-600 border-green-300 hover:bg-green-50"
                                                            onClick={() => handleStatusChange(apt.appointment_id, "completed")}
                                                        >
                                                            Marquer terminé
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            className="text-red-600 border-red-300 hover:bg-red-50"
                                                            onClick={() => handleStatusChange(apt.appointment_id, "cancelled")}
                                                        >
                                                            Annuler
                                                        </Button>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </div>
            )}
        </div>
    );
}
