"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    Users,
    FileText,
    Calendar,
    Server,
    Activity,
    ArrowRight,
    MessageSquare,
    Stethoscope,
    Sparkles
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { Entity, Doctor, Instance, KBDocument } from "@/types";

// Extended types for stats
interface DashboardStats {
    doctorCount: number;
    docCount: number;
    instanceCount: number;
    appointmentCount: number;
}

export default function EntityHome() {
    const params = useParams();
    const router = useRouter();
    const entityId = params.id as string;
    const { currentEntity, setCurrentEntity } = useAppStore();

    const [stats, setStats] = useState<DashboardStats>({
        doctorCount: 0,
        docCount: 0,
        instanceCount: 0,
        appointmentCount: 0
    });
    const [isLoading, setIsLoading] = useState(true);
    const [recentActivity, setRecentActivity] = useState<any[]>([]); // Mock for now or real if available

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                setIsLoading(true);

                // Parallel fetching
                const [entityRes, doctorsRes, kbRes, instancesRes, apptRes] = await Promise.all([
                    api.get<Entity>(`/entities/${entityId}`),
                    api.get<Doctor[]>("/doctors/"),
                    api.get<KBDocument[]>(`/kb/documents/${entityId}`),
                    api.get<Instance[]>("/instances"),
                    api.get<any[]>("/appointments") // Assuming this endpoint returns all appointments, we filter client side 
                    // Note: Real prod would use specific stats endpoints to avoid over-fetching
                ]);

                setCurrentEntity(entityRes.data);

                // Filter data for this entity
                const doctors = (doctorsRes.data || []).filter((d: any) => d.entity_id === entityId);
                const instances = (instancesRes.data || []).filter((i: any) => i.entity_id === entityId);
                const appointments = (apptRes.data || []).filter((a: any) =>
                    // Filter if appointment has doctor that belongs to entity
                    doctors.some((d: any) => d.doctor_id === a.doctor_id)
                );

                setStats({
                    doctorCount: doctors.length,
                    docCount: (kbRes.data || []).length,
                    instanceCount: instances.length,
                    appointmentCount: appointments.length
                });

                // Mock recent activity from real appointments (latest 3)
                const recent = appointments
                    .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                    .slice(0, 3)
                    .map((a: any) => ({
                        id: a.appointment_id,
                        type: 'appointment',
                        title: `Rendez-vous : ${a.patient_name}`,
                        desc: `Avec Dr. ${a.doctor ? a.doctor.last_name : 'Inconnu'} - ${new Date(a.date).toLocaleDateString()}`,
                        time: new Date(a.created_at),
                        status: a.status
                    }));

                setRecentActivity(recent);

            } catch (error) {
                console.error("Dashboard fetch error", error);
            } finally {
                setIsLoading(false);
            }
        };

        if (entityId) {
            fetchDashboardData();
        }
    }, [entityId, setCurrentEntity]);

    const QuickActionCard = ({ title, icon: Icon, color, onClick, desc }: any) => (
        <div
            onClick={onClick}
            className="group relative overflow-hidden rounded-xl bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md cursor-pointer border border-slate-100"
        >
            <div className={`absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-10 transition-transform group-hover:scale-150 ${color}`} />
            <div className="relative z-10">
                <div className={`mb-4 inline-flex rounded-lg p-3 ${color} bg-opacity-10 text-white shadow-sm`}>
                    <Icon className={`h-6 w-6 ${color.replace('bg-', 'text-')}`} />
                </div>
                <h3 className="mb-1 text-lg font-semibold text-slate-800">{title}</h3>
                <p className="text-sm text-slate-500">{desc}</p>
            </div>
            <div className="absolute bottom-4 right-4 opacity-0 transition-opacity group-hover:opacity-100">
                <ArrowRight className="h-5 w-5 text-slate-400" />
            </div>
        </div>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-slate-900">
                        Tableau de bord
                    </h1>
                    <p className="text-slate-500">
                        Bienvenue sur la gestion de <span className="font-semibold text-indigo-600">{currentEntity?.name || "..."}</span>
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="flex h-2 w-2 rounded-full bg-green-500"></span>
                    <span className="text-sm font-medium text-slate-600">Système opérationnel</span>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card className="border-l-4 border-l-indigo-500 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500">Médecins</CardTitle>
                        <Stethoscope className="h-4 w-4 text-indigo-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-slate-800">{isLoading ? "-" : stats.doctorCount}</div>
                        <p className="text-xs text-slate-400">Praticiens actifs</p>
                    </CardContent>
                </Card>
                <Card className="border-l-4 border-l-purple-500 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500">Connaissances</CardTitle>
                        <FileText className="h-4 w-4 text-purple-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-slate-800">{isLoading ? "-" : stats.docCount}</div>
                        <p className="text-xs text-slate-400">Documents indexés</p>
                    </CardContent>
                </Card>
                <Card className="border-l-4 border-l-amber-500 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500">Rendez-vous</CardTitle>
                        <Calendar className="h-4 w-4 text-amber-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-slate-800">{isLoading ? "-" : stats.appointmentCount}</div>
                        <p className="text-xs text-slate-400">Total réservations</p>
                    </CardContent>
                </Card>
                <Card className="border-l-4 border-l-cyan-500 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-500">Instances</CardTitle>
                        <Server className="h-4 w-4 text-cyan-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-slate-800">{isLoading ? "-" : stats.instanceCount}</div>
                        <p className="text-xs text-slate-400">Canaux actifs</p>
                    </CardContent>
                </Card>
            </div>

            {/* Quick Actions */}
            <div>
                <h2 className="mb-4 text-lg font-semibold text-slate-800">Actions Rapides</h2>
                <div className="grid gap-6 md:grid-cols-3">
                    <QuickActionCard
                        title="Tester le Chatbot"
                        desc="Lancez une conversation de test avec l'IA configurée."
                        icon={Sparkles}
                        color="bg-indigo-600"
                        onClick={() => router.push(`/entity/${entityId}/test`)}
                    />
                    <QuickActionCard
                        title="Base de Connaissance"
                        desc="Ajoutez ou modifiez les documents de référence."
                        icon={FileText}
                        color="bg-purple-600"
                        onClick={() => router.push(`/entity/${entityId}/knowledge`)}
                    />
                    <QuickActionCard
                        title="Gérer le Personnel"
                        desc="Ajoutez des médecins et gérez les plannings."
                        icon={Users}
                        color="bg-slate-600"
                        onClick={() => router.push(`/entity/${entityId}/staff`)}
                    />
                </div>
            </div>

            {/* Recent Activity */}
            <div className="grid gap-6 md:grid-cols-7">
                <div className="md:col-span-4 rounded-xl border bg-white shadow-sm">
                    <div className="flex items-center justify-between border-b p-4">
                        <h3 className="font-semibold text-slate-800">Activité Récente</h3>
                        <Activity className="h-4 w-4 text-slate-400" />
                    </div>
                    <div className="p-4">
                        {isLoading ? (
                            <div className="space-y-3">
                                {[1, 2, 3].map(i => <div key={i} className="h-16 w-full animate-pulse rounded-lg bg-slate-50" />)}
                            </div>
                        ) : recentActivity.length > 0 ? (
                            <div className="space-y-4">
                                {recentActivity.map((activity, i) => (
                                    <div key={i} className="flex items-center gap-4 rounded-lg border border-slate-50 bg-slate-50/50 p-3 transition-colors hover:bg-white hover:border-indigo-100 hover:shadow-sm">
                                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white shadow-sm text-indigo-600">
                                            {activity.type === 'appointment' ? <Calendar className="h-5 w-5" /> : <Activity className="h-5 w-5" />}
                                        </div>
                                        <div className="flex-1">
                                            <p className="text-sm font-medium text-slate-900">{activity.title}</p>
                                            <p className="text-xs text-slate-500">{activity.desc}</p>
                                        </div>
                                        <div className="text-right">
                                            <Badge variant={activity.status === 'confirmed' ? "default" : "secondary"} className="text-[10px]">
                                                {activity.status}
                                            </Badge>
                                            <p className="mt-1 text-[10px] text-slate-400">
                                                {new Date(activity.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center py-10 text-slate-400">
                                <Activity className="mb-2 h-8 w-8 opacity-20" />
                                <p className="text-sm">Aucune activité récente.</p>
                            </div>
                        )}
                    </div>
                </div>

                <div className="md:col-span-3 rounded-xl border bg-gradient-to-br from-slate-900 to-slate-800 p-6 text-white shadow-lg">
                    <div className="mb-6">
                        <h3 className="text-lg font-semibold">Statut du Système</h3>
                        <p className="text-sm text-slate-400">Tout fonctionne normalement.</p>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <span className="text-sm text-slate-300">API Latence</span>
                            <span className="font-mono text-sm text-green-400">24ms</span>
                        </div>
                        <div className="h-1 w-full rounded-full bg-slate-700">
                            <div className="h-1 w-[20%] rounded-full bg-green-400"></div>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                            <span className="text-sm text-slate-300">Base de Données</span>
                            <span className="font-mono text-sm text-green-400">Connecté</span>
                        </div>
                        <div className="h-1 w-full rounded-full bg-slate-700">
                            <div className="h-1 w-full rounded-full bg-green-400"></div>
                        </div>

                        <div className="flex items-center justify-between pt-2">
                            <span className="text-sm text-slate-300">Modèles IA</span>
                            <span className="font-mono text-sm text-indigo-400">OpenAI Actif</span>
                        </div>
                    </div>

                    <div className="mt-8 rounded-lg bg-white/10 p-3 backdrop-blur-sm">
                        <p className="text-xs text-slate-300">
                            <span className="font-bold text-white">Note:</span> Le système de rappel automatique par SMS est désactivé.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
