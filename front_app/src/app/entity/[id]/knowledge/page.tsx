"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Trash2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { UploadBox } from "@/components/UploadBox";
import api from "@/lib/api";
import { KnowledgeChunk } from "@/types";

export default function KnowledgePage() {
    const params = useParams();
    const entityId = params.id as string;
    const [chunks, setChunks] = useState<KnowledgeChunk[]>([]);

    const fetchChunks = async () => {
        try {
            const res = await api.get<KnowledgeChunk[]>(`/knowledge/${entityId}`);
            setChunks(res.data);
        } catch (error) {
            console.error("Failed to fetch knowledge", error);
        }
    };

    useEffect(() => {
        if (entityId) {
            fetchChunks();
        }
    }, [entityId]);

    const handleUpload = async (files: FileList) => {
        const formData = new FormData();
        formData.append("file", files[0]);
        formData.append("entity_id", entityId);

        try {
            await api.post("/knowledge/upload", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            fetchChunks();
        } catch (error) {
            console.error("Failed to upload file", error);
            alert("Erreur lors de l'upload");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Supprimer ce chunk ?")) return;
        try {
            await api.delete(`/knowledge/${id}`);
            fetchChunks();
        } catch (error) {
            console.error("Failed to delete chunk", error);
        }
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight">Base de Connaissance</h1>

            <div className="grid gap-6 md:grid-cols-3">
                <div className="md:col-span-1">
                    <div className="rounded-lg border bg-white p-4 shadow-sm">
                        <h2 className="mb-4 text-lg font-semibold">Ajouter un document</h2>
                        <UploadBox onUpload={handleUpload} accept=".pdf,.txt,.docx" />
                        <p className="mt-2 text-xs text-muted-foreground">
                            Formats supportés : PDF, TXT, DOCX. Le fichier sera découpé et vectorisé.
                        </p>
                    </div>
                </div>

                <div className="md:col-span-2">
                    <div className="rounded-md border bg-white">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Source</TableHead>
                                    <TableHead>Contenu (extrait)</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {chunks.map((chunk) => (
                                    <TableRow key={chunk.chunk_id}>
                                        <TableCell className="font-medium">
                                            <div className="flex items-center">
                                                <FileText className="mr-2 h-4 w-4 text-muted-foreground" />
                                                {chunk.source_doc}
                                            </div>
                                        </TableCell>
                                        <TableCell className="max-w-md truncate">
                                            {chunk.content}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-red-500 hover:text-red-700"
                                                onClick={() => handleDelete(chunk.chunk_id)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {chunks.length === 0 && (
                                    <TableRow>
                                        <TableCell colSpan={3} className="h-24 text-center">
                                            Aucune connaissance enregistrée.
                                        </TableCell>
                                    </TableRow>
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </div>
        </div>
    );
}
