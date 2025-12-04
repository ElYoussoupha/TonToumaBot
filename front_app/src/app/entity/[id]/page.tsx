"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Database, Server, MessageSquare } from "lucide-react";
import api from "@/lib/api";
import { useAppStore } from "@/lib/store";
import { Entity } from "@/types";

export default function EntityHome() {
    const params = useParams();
    const entityId = params.id as string;
    const { setCurrentEntity } = useAppStore();

    useEffect(() => {
        const fetchEntity = async () => {
            try {
                const res = await api.get<Entity>(`/entities/${entityId}`);
                setCurrentEntity(res.data);
            } catch (error) {
                console.error("Failed to fetch entity", error);
            }
        };

        if (entityId) {
            fetchEntity();
        }
    }, [entityId, setCurrentEntity]);

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Vue d'ensemble</h1>

            <div className="grid gap-4 md:grid-cols-3">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Base de Connaissance</CardTitle>
                        <Database className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">--</div>
                        <p className="text-xs text-muted-foreground">Documents indexés</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Instances</CardTitle>
                        <Server className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">--</div>
                        <p className="text-xs text-muted-foreground">Points de contact</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Sessions</CardTitle>
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">--</div>
                        <p className="text-xs text-muted-foreground">Conversations totales</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
