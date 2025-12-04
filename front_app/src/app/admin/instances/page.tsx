"use client";

import { useState, useEffect } from "react";
import { Plus, Search, Trash2 } from "lucide-react";
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
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Entity, Instance } from "@/types";

export default function InstancesPage() {
    const [instances, setInstances] = useState<Instance[]>([]);
    const [entities, setEntities] = useState<Entity[]>([]);
    const [search, setSearch] = useState("");
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [newInstance, setNewInstance] = useState({
        name: "",
        entity_id: "",
        location: "",
        status: "active",
    });

    const fetchData = async () => {
        try {
            const [instancesRes, entitiesRes] = await Promise.all([
                api.get<Instance[]>("/instances"),
                api.get<Entity[]>("/entities"),
            ]);
            setInstances(instancesRes.data);
            setEntities(entitiesRes.data);
        } catch (error) {
            console.error("Failed to fetch data", error);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleCreate = async () => {
        try {
            await api.post("/instances", newInstance);
            setIsCreateOpen(false);
            setNewInstance({ name: "", entity_id: "", location: "", status: "active" });
            fetchData();
        } catch (error) {
            console.error("Failed to create instance", error);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer cette instance ?")) return;
        try {
            await api.delete(`/instances/${id}`);
            fetchData();
        } catch (error) {
            console.error("Failed to delete instance", error);
        }
    };

    const filteredInstances = instances.filter((i) =>
        i.name.toLowerCase().includes(search.toLowerCase())
    );

    const getEntityName = (id: string) => {
        return entities.find((e) => e.entity_id === id)?.name || id;
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Instances</h1>
                <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
                    <DialogTrigger asChild>
                        <Button>
                            <Plus className="mr-2 h-4 w-4" /> Nouvelle Instance
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Créer une nouvelle instance</DialogTitle>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid gap-2">
                                <Label htmlFor="entity">Entité</Label>
                                <Select
                                    onValueChange={(val) => setNewInstance({ ...newInstance, entity_id: val })}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="Sélectionner une entité" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {entities.map((e) => (
                                            <SelectItem key={e.entity_id} value={e.entity_id}>
                                                {e.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="name">Nom</Label>
                                <Input
                                    id="name"
                                    value={newInstance.name}
                                    onChange={(e) => setNewInstance({ ...newInstance, name: e.target.value })}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="location">Localisation</Label>
                                <Input
                                    id="location"
                                    value={newInstance.location}
                                    onChange={(e) => setNewInstance({ ...newInstance, location: e.target.value })}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleCreate} disabled={!newInstance.entity_id}>
                                Créer
                            </Button>
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
                            <TableHead>Entité</TableHead>
                            <TableHead>Localisation</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {filteredInstances.map((instance) => (
                            <TableRow key={instance.instance_id}>
                                <TableCell className="font-medium">{instance.name}</TableCell>
                                <TableCell>{getEntityName(instance.entity_id)}</TableCell>
                                <TableCell>{instance.location}</TableCell>
                                <TableCell>
                                    <Badge variant={instance.status === "active" ? "default" : "secondary"}>
                                        {instance.status}
                                    </Badge>
                                </TableCell>
                                <TableCell className="text-right">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        className="text-red-500 hover:text-red-700"
                                        onClick={() => handleDelete(instance.instance_id)}
                                    >
                                        <Trash2 className="h-4 w-4" />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                        {filteredInstances.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={5} className="h-24 text-center">
                                    Aucune instance trouvée.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
        </div>
    );
}
