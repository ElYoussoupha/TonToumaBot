"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import api from "@/lib/api";
import { Instance } from "@/types";

export default function EntityInstancesPage() {
    const params = useParams();
    const entityId = params.id as string;
    const [instances, setInstances] = useState<Instance[]>([]);

    useEffect(() => {
        const fetchInstances = async () => {
            try {
                const res = await api.get<Instance[]>("/instances");
                // Filter client-side for now if backend doesn't support filtering by entity
                const entityInstances = res.data.filter(i => i.entity_id === entityId);
                setInstances(entityInstances);
            } catch (error) {
                console.error("Failed to fetch instances", error);
            }
        };

        if (entityId) {
            fetchInstances();
        }
    }, [entityId]);

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Instances déployées</h1>

            <div className="rounded-md border bg-white">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Nom</TableHead>
                            <TableHead>Localisation</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Dernier Heartbeat</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {instances.map((instance) => (
                            <TableRow key={instance.instance_id}>
                                <TableCell className="font-medium">{instance.name}</TableCell>
                                <TableCell>{instance.location}</TableCell>
                                <TableCell>
                                    <Badge variant={instance.status === "active" ? "default" : "secondary"}>
                                        {instance.status}
                                    </Badge>
                                </TableCell>
                                <TableCell>{instance.last_heartbeat || "-"}</TableCell>
                            </TableRow>
                        ))}
                        {instances.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    Aucune instance pour cette entité.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
