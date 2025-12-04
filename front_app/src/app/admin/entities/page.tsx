"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Plus, Search, ExternalLink, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
    DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import api from "@/lib/api";
import { Entity } from "@/types";

export default function EntitiesPage() {
    const [entities, setEntities] = useState<Entity[]>([]);
    const [search, setSearch] = useState("");
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newEntity, setNewEntity] = useState({ name: "", description: "", contact_email: "" });

    const fetchEntities = async () => {
        try {
            const res = await api.get<Entity[]>("/entities");
            setEntities(res.data);
        } catch (error) {
            console.error("Failed to fetch entities", error);
        }
    };

    useEffect(() => {
        fetchEntities();
    }, []);

    const handleCreate = async () => {
        try {
            await api.post("/entities", newEntity);
            setIsCreateOpen(false);
            setNewEntity({ name: "", description: "", contact_email: "" });
            fetchEntities();
        } catch (error) {
            console.error("Failed to create entity", error);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer cette entité ?")) return;
        try {
            await api.delete(`/entities/${id}`);
            fetchEntities();
        } catch (error) {
            console.error("Failed to delete entity", error);
        }
    };

    const filteredEntities = entities.filter((e) =>
        e.name.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Entités</h1>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Nouvelle Entité
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Créer une nouvelle entité</DialogTitle>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="name">Nom</Label>
                                <Input
                                    id="name"
                                    value={newEntity.name}
                                    onChange={(e) => setNewEntity({ ...newEntity, name: e.target.value })}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="description">Description</Label>
                                <Input
                                    id="description"
                                    value={newEntity.description}
                                    onChange={(e) => setNewEntity({ ...newEntity, description: e.target.value })}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="email">Email de contact</Label>
                                <Input
                                    id="email"
                                    value={newEntity.contact_email}
                                    onChange={(e) => setNewEntity({ ...newEntity, contact_email: e.target.value })}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleCreate}>Créer</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>

            <div className="flex items-center space-x-2">
                <Search className="h-4 w-4 text-muted-foreground" />
                <Input
                    placeholder="Rechercher..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="max-w-sm"
                />
            </div>

            <div className="rounded-md border bg-white">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Nom</TableHead>
                            <TableHead>Description</TableHead>
                            <TableHead>Email</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredEntities.map((entity) => (
                            <TableRow key={entity.entity_id}>
                                <TableCell className="font-medium">{entity.name}</TableCell>
                                <TableCell>{entity.description}</TableCell>
                                <TableCell>{entity.contact_email}</TableCell>
                                <TableCell className="text-right">
                                    <div className="flex justify-end space-x-2">
                                        <Link href={`/entity/${entity.entity_id}`}>
                                            <Button variant="ghost" size="icon">
                                                <ExternalLink className="h-4 w-4" />
                                            </Button>
                                        </Link>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="text-red-500 hover:text-red-700"
                                            onClick={() => handleDelete(entity.entity_id)}
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                        {filteredEntities.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="h-24 text-center">
                                    Aucune entité trouvée.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
