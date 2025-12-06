"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, Users, CheckCircle } from "lucide-react";
import api from "@/lib/api";
import { Appointment, TimeSlot } from "@/types";

export default function DoctorDashboard() {
    const [appointments, setAppointments] = useState<Appointment[]>([]);
    const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [doctorName, setDoctorName] = useState("");

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
            const today = new Date().toISOString().split("T")[0];
            const [apptRes, slotsRes] = await Promise.all([
                api.get<Appointment[]>(`/appointments?doctor_id=${doctorId}&date=${today}`),
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

    const todayAppointments = appointments.filter(
        (a) => a.status !== "cancelled"
    ).sort((a, b) => a.start_time.localeCompare(b.start_time));

    const pendingCount = appointments.filter((a) => a.status === "pending").length;
    const confirmedCount = appointments.filter((a) => a.status === "confirmed").length;

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">
                    Bonjour, Dr. {doctorName.split(" ")[1] || doctorName}
                </h1>
                <p className="text-muted-foreground">
                    Voici votre planning pour aujourd'hui
                </p>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">RDV aujourd'hui</CardTitle>
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{todayAppointments.length}</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">En attente</CardTitle>
                        <Clock className="h-4 w-4 text-yellow-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-yellow-600">{pendingCount}</div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Confirmés</CardTitle>
                        <CheckCircle className="h-4 w-4 text-green-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-green-600">{confirmedCount}</div>
                    </CardContent>
                </Card>
            </div>

            {/* Today's Appointments */}
            <Card>
                <CardHeader>
                    <CardTitle>Rendez-vous du jour</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <p className="text-center text-muted-foreground py-4">Chargement...</p>
                    ) : todayAppointments.length === 0 ? (
                        <p className="text-center text-muted-foreground py-8">
                            Aucun rendez-vous prévu aujourd'hui
                        </p>
                    ) : (
                        <div className="space-y-4">
                            {todayAppointments.map((appt) => (
                                <div
                                    key={appt.appointment_id}
                                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="h-12 w-12 rounded-full bg-emerald-100 flex items-center justify-center">
                                            <Users className="h-6 w-6 text-emerald-600" />
                                        </div>
                                        <div>
                                            <p className="font-medium">{appt.patient_name}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {appt.reason}
                                            </p>
                                            <p className="text-sm text-muted-foreground">
                                                {appt.patient_email}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="font-medium text-lg">
                                            {appt.start_time.slice(0, 5)}
                                        </p>
                                        <Badge variant={
                                            appt.status === "confirmed" ? "default" :
                                                appt.status === "pending" ? "secondary" :
                                                    "destructive"
                                        }>
                                            {appt.status === "pending" ? "En attente" :
                                                appt.status === "confirmed" ? "Confirmé" :
                                                    appt.status === "completed" ? "Terminé" :
                                                        "Annulé"}
                                        </Badge>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
                <CardHeader>
                    <CardTitle>Mes créneaux configurés</CardTitle>
                </CardHeader>
                <CardContent>
                    {timeSlots.length === 0 ? (
                        <p className="text-center text-muted-foreground py-4">
                            Aucun créneau configuré. Allez dans "Mes créneaux" pour en ajouter.
                        </p>
                    ) : (
                        <div className="flex flex-wrap gap-2">
                            {["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"].map((day, index) => {
                                const hasSlot = timeSlots.some(
                                    (s) => s.is_recurring && s.day_of_week === index
                                );
                                return (
                                    <Badge
                                        key={day}
                                        variant={hasSlot ? "default" : "outline"}
                                        className={hasSlot ? "bg-emerald-600" : ""}
                                    >
                                        {day}
                                    </Badge>
                                );
                            })}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
