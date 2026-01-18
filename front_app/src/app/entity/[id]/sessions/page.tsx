"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { MessageSquare, User } from "lucide-react";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Session } from "@/types";

export default function EntitySessionsPage() {
    const params = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const entityId = params["id"] as string;
    const instanceIdFilter = searchParams.get("instance_id");

    const [sessions, setSessions] = useState<Session[]>([]);

    useEffect(() => {
        const fetchSessions = async () => {
            try {
                const res = await api.get<Session[]>(`/sessions?entity_id=${entityId}`);
                let data = res.data;

                if (instanceIdFilter) {
                    // Start of workaround: If backend doesn't support exact instance filtering on this endpoint yet, do it here.
                    // But wait, the Session model DOES have instance_id.
                    // Ideally check backend support. Assuming backend returns all entity sessions, we filter here.
                    // Actually, let's filter client side for now to be safe.
                    // NOTE: The Session type definition in frontend might need instance_id field if not present.
                    // Assuming it is present or we rely on backend improvements later.
                    // Let's rely on client-side filtering safely.
                    data = data.filter((s: any) => s.instance_id === instanceIdFilter || s.instance?.instance_id === instanceIdFilter);
                }
                setSessions(data);
            } catch (error) {
                console.error("Failed to fetch sessions", error);
            }
        };

        if (entityId) {
            fetchSessions();
        }
    }, [entityId]);

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Sessions</h1>

            <div className="rounded-md border bg-white">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Session ID</TableHead>
                            <TableHead>Interlocuteur</TableHead>
                            <TableHead>Début</TableHead>
                            <TableHead>Status</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {sessions.map((session) => (
                            <TableRow
                                key={session.session_id}
                                className="cursor-pointer hover:bg-muted/50"
                                onClick={() => router.push(`/entity/${entityId}/sessions/${session.session_id}`)}
                            >
                                <TableCell className="font-mono text-xs text-blue-600">{session.session_id}</TableCell>
                                <TableCell>
                                    <div className="flex items-center">
                                        <User className="mr-2 h-4 w-4 text-muted-foreground" />
                                        {session.speaker_id ? "Identifié" : "Anonyme"}
                                    </div>
                                </TableCell>
                                <TableCell>{new Date(session.start_time).toLocaleString()}</TableCell>
                                <TableCell>
                                    <Badge variant={session.is_active ? "default" : "outline"}>
                                        {session.is_active ? "En cours" : "Terminée"}
                                    </Badge>
                                </TableCell>
                            </TableRow>
                        ))}
                        {sessions.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    Aucune session trouvée.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
