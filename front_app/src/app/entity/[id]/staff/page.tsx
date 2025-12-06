"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Plus, User, Mail, Phone, Clock, Copy, Check } from "lucide-react";
import api from "@/lib/api";
import { Doctor, DoctorCredentials, Specialty } from "@/types";

export default function StaffPage() {
    const params = useParams();
    const entityId = params.id as string;

    const [doctors, setDoctors] = useState<Doctor[]>([]);
    const [specialties, setSpecialties] = useState<Specialty[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [showCredentials, setShowCredentials] = useState<DoctorCredentials | null>(null);
    const [copied, setCopied] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        first_name: "",
        last_name: "",
        email: "",
        phone: "",
        specialty_id: "",
        consultation_duration: 30
    });

    useEffect(() => {
        fetchData();
    }, [entityId]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [doctorsRes, specialtiesRes] = await Promise.all([
                api.get<Doctor[]>(`/doctors?entity_id=${entityId}`),
                api.get<Specialty[]>("/specialties")
            ]);
            setDoctors(doctorsRes.data || []);
            setSpecialties(specialtiesRes.data || []);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await api.post<DoctorCredentials>("/doctors", {
                ...formData,
                entity_id: entityId,
                specialty_id: formData.specialty_id || null
            });
            setShowCredentials(res.data);
            setShowForm(false);
            setFormData({
                first_name: "",
                last_name: "",
                email: "",
                phone: "",
                specialty_id: "",
                consultation_duration: 30
            });
            fetchData();
        } catch (error) {
            console.error("Failed to create doctor", error);
            alert("Erreur lors de la création du médecin");
        }
    };

    const copyCredentials = () => {
        if (showCredentials) {
            navigator.clipboard.writeText(
                `Email: ${showCredentials.email}\nMot de passe: ${showCredentials.temporary_password}`
            );
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold tracking-tight">Gestion du Personnel</h1>
                <Button onClick={() => setShowForm(true)}>
                    <Plus className="mr-2 h-4 w-4" />
                    Ajouter un médecin
                </Button>
            </div>

            {/* Credentials Modal */}
            {showCredentials && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-md mx-4">
                        <CardHeader>
                            <CardTitle className="text-green-600">Médecin créé avec succès !</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <p className="text-sm text-muted-foreground">
                                {showCredentials.message}
                            </p>
                            <div className="bg-slate-100 rounded-lg p-4 space-y-2">
                                <div className="flex justify-between">
                                    <span className="font-medium">Email:</span>
                                    <span className="font-mono">{showCredentials.email}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="font-medium">Mot de passe:</span>
                                    <span className="font-mono">{showCredentials.temporary_password}</span>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <Button variant="outline" className="flex-1" onClick={copyCredentials}>
                                    {copied ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}
                                    {copied ? "Copié !" : "Copier"}
                                </Button>
                                <Button className="flex-1" onClick={() => setShowCredentials(null)}>
                                    Fermer
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Add Doctor Form Modal */}
            {showForm && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <Card className="w-full max-w-lg mx-4">
                        <CardHeader>
                            <CardTitle>Ajouter un médecin</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="first_name">Prénom</Label>
                                        <Input
                                            id="first_name"
                                            value={formData.first_name}
                                            onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="last_name">Nom</Label>
                                        <Input
                                            id="last_name"
                                            value={formData.last_name}
                                            onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="phone">Téléphone</Label>
                                    <Input
                                        id="phone"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="specialty">Spécialité</Label>
                                    <select
                                        id="specialty"
                                        className="w-full rounded-md border border-input bg-background px-3 py-2"
                                        value={formData.specialty_id}
                                        onChange={(e) => setFormData({ ...formData, specialty_id: e.target.value })}
                                    >
                                        <option value="">-- Aucune --</option>
                                        {specialties.map((s) => (
                                            <option key={s.specialty_id} value={s.specialty_id}>
                                                {s.name}
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="duration">Durée de consultation (minutes)</Label>
                                    <Input
                                        id="duration"
                                        type="number"
                                        min={10}
                                        max={120}
                                        value={formData.consultation_duration}
                                        onChange={(e) => setFormData({ ...formData, consultation_duration: parseInt(e.target.value) })}
                                    />
                                </div>

                                <div className="flex gap-2 pt-4">
                                    <Button type="button" variant="outline" className="flex-1" onClick={() => setShowForm(false)}>
                                        Annuler
                                    </Button>
                                    <Button type="submit" className="flex-1">
                                        Créer
                                    </Button>
                                </div>
                            </form>
                        </CardContent>
                    </Card>
                </div>
            )}

            {/* Doctors List */}
            {isLoading ? (
                <div className="text-center py-8 text-muted-foreground">Chargement...</div>
            ) : doctors.length === 0 ? (
                <Card>
                    <CardContent className="py-8 text-center text-muted-foreground">
                        Aucun médecin enregistré. Cliquez sur "Ajouter un médecin" pour commencer.
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {doctors.map((doctor) => (
                        <Card key={doctor.doctor_id} className="hover:shadow-md transition-shadow">
                            <CardHeader className="pb-2">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-lg">
                                        Dr. {doctor.first_name} {doctor.last_name}
                                    </CardTitle>
                                    <Badge variant={doctor.is_active ? "default" : "secondary"}>
                                        {doctor.is_active ? "Actif" : "Inactif"}
                                    </Badge>
                                </div>
                                {doctor.specialty_name && (
                                    <p className="text-sm text-indigo-600">{doctor.specialty_name}</p>
                                )}
                            </CardHeader>
                            <CardContent className="space-y-2">
                                <div className="flex items-center text-sm text-muted-foreground">
                                    <Mail className="mr-2 h-4 w-4" />
                                    {doctor.email}
                                </div>
                                {doctor.phone && (
                                    <div className="flex items-center text-sm text-muted-foreground">
                                        <Phone className="mr-2 h-4 w-4" />
                                        {doctor.phone}
                                    </div>
                                )}
                                <div className="flex items-center text-sm text-muted-foreground">
                                    <Clock className="mr-2 h-4 w-4" />
                                    {doctor.consultation_duration} min / consultation
                                </div>
                                <div className="pt-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        className="w-full"
                                        onClick={() => window.location.href = `/entity/${entityId}/staff/${doctor.doctor_id}`}
                                    >
                                        Gérer le planning
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
