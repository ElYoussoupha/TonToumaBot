"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Server, MessageSquare, Activity } from "lucide-react";
import api from "@/lib/api";
import { Entity, Instance } from "@/types";

export default function AdminDashboard() {
    const [stats, setStats] = useState({
        entities: 0,
        instances: 0,
        activeSessions: 0,
    });

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const [entitiesRes, instancesRes] = await Promise.all([
                    api.get<Entity[]>("/entities"),
                    api.get<Instance[]>("/instances"),
                ]);

                // Mock active sessions for now as endpoint might not exist
                const activeSessions = 0;

                setStats({
                    entities: entitiesRes.data.length,
                    instances: instancesRes.data.length,
                    activeSessions,
                });
            } catch (error) {
                console.error("Failed to fetch stats", error);
            }
        };

        fetchStats();
    }, []);

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Entités</CardTitle>
                        <Users className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.entities}</div>
                        <p className="text-xs text-muted-foreground">Organisations enregistrées</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Instances Actives</CardTitle>
                        <Server className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.instances}</div>
                        <p className="text-xs text-muted-foreground">Chatbots déployés</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Sessions en cours</CardTitle>
                        <Activity className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats.activeSessions}</div>
                        <p className="text-xs text-muted-foreground">Conversations actives</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Messages (24h)</CardTitle>
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">0</div>
                        <p className="text-xs text-muted-foreground">Interactions totales</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
