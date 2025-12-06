"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { Trash2, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
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
import { KBDocument } from "@/types";

export default function KnowledgePage() {
    const params = useParams();
    const entityId = params.id as string;
    const [documents, setDocuments] = useState<KBDocument[]>([]);
    const [textTitle, setTextTitle] = useState<string>("");
    const [textContent, setTextContent] = useState<string>("");
    const [isSubmittingText, setIsSubmittingText] = useState<boolean>(false);

    const fetchDocuments = useCallback(async () => {
        try {
            const res = await api.get<KBDocument[]>(`/kb/documents/${entityId}`);
            setDocuments(res.data);
        } catch (error) {
            console.error("Failed to fetch documents", error);
        }
    }, [entityId]);

    const handleSubmitText = async () => {
        if (!textTitle.trim() || !textContent.trim()) {
            alert("Veuillez renseigner le titre et le contenu.");
            return;
        }
        setIsSubmittingText(true);
        try {
            const formData = new FormData();
            formData.append("title", textTitle.trim());
            formData.append("content", textContent);
            formData.append("entity_id", entityId);
            await api.post("/kb/text", formData);
            setTextTitle("");
            setTextContent("");
            alert("Document texte ajouté avec succès !");
            fetchDocuments();
        } catch (error) {
            console.error("Failed to submit text document", error);
            alert("Erreur lors de l'ajout du document texte.");
        } finally {
            setIsSubmittingText(false);
        }
    };

    useEffect(() => {
        if (entityId) {
            fetchDocuments();
        }
    }, [entityId, fetchDocuments]);

    const handleUpload = async (files: FileList) => {
        const file = files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("file", file);
        formData.append("title", file.name); // Default title to filename
        formData.append("entity_id", entityId);

        try {
            await api.post("/kb/documents", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            });
            alert("Document ajouté avec succès !");
            fetchDocuments();
        } catch (error) {
            console.error("Failed to upload file", error);
            alert("Erreur lors de l'upload du document.");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Supprimer ce document ?")) return;
        try {
            await api.delete(`/kb/documents/${id}`);
            alert("Document supprimé avec succès !");
            fetchDocuments();
        } catch (error) {
            console.error("Failed to delete document", error);
            alert("Erreur lors de la suppression du document.");
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
                        <div className="mt-6 h-px w-full bg-slate-200" />
                        <h3 className="mt-4 mb-2 text-sm font-medium">Ou créer depuis un texte</h3>
                        <div className="space-y-3">
                            <Input
                                placeholder="Titre du document"
                                value={textTitle}
                                onChange={(e) => setTextTitle(e.target.value)}
                            />
                            <Textarea
                                placeholder="Collez ou écrivez ici votre contenu..."
                                className="min-h-[160px]"
                                value={textContent}
                                onChange={(e) => setTextContent(e.target.value)}
                            />
                            <Button onClick={handleSubmitText} disabled={isSubmittingText}>
                                {isSubmittingText ? "Ajout..." : "Ajouter le texte"}
                            </Button>
                        </div>
                    </div>
                </div>

                <div className="md:col-span-2">
                    <div className="rounded-md border bg-white">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Document</TableHead>
                                    <TableHead>Contenu (Aperçu)</TableHead>
                                    <TableHead className="text-right">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {documents.map((doc) => (
                                    <TableRow key={doc.doc_id}>
                                        <TableCell className="font-medium">
                                            <div className="flex items-center">
                                                <FileText className="mr-2 h-4 w-4 text-muted-foreground" />
                                                {doc.title}
                                            </div>
                                        </TableCell>
                                        <TableCell className="max-w-md truncate">
                                            {doc.chunks && doc.chunks.length > 0
                                                ? doc.chunks[0].content.substring(0, 100) + "..."
                                                : "Pas de contenu"}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="text-red-500 hover:text-red-700"
                                                onClick={() => handleDelete(doc.doc_id)}
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                                {documents.length === 0 && (
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
