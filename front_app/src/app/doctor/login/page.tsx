"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Stethoscope, Mail, Lock } from "lucide-react";
import api from "@/lib/api";

interface DoctorLoginResponse {
    doctor_id: string;
    first_name: string;
    last_name: string;
    entity_id: string;
    specialty_id?: string;
    token: string;
}

export default function DoctorLoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const res = await api.post<DoctorLoginResponse>("/doctors/login", {
                email,
                password
            });

            // Store doctor info in localStorage
            localStorage.setItem("doctor_token", res.data.token);
            localStorage.setItem("doctor_id", res.data.doctor_id);
            localStorage.setItem("doctor_name", `${res.data.first_name} ${res.data.last_name}`);
            localStorage.setItem("doctor_entity_id", res.data.entity_id);

            // Redirect to doctor dashboard
            router.push("/doctor");
        } catch (err: any) {
            console.error("Login failed", err);
            if (err.response?.status === 401) {
                setError("Email ou mot de passe incorrect");
            } else {
                setError("Erreur de connexion. Veuillez réessayer.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-100 to-purple-100 p-4">
            <Card className="w-full max-w-md shadow-xl">
                <CardHeader className="text-center">
                    <div className="mx-auto mb-4 h-16 w-16 rounded-full bg-indigo-600 flex items-center justify-center">
                        <Stethoscope className="h-8 w-8 text-white" />
                    </div>
                    <CardTitle className="text-2xl">Espace Médecin</CardTitle>
                    <CardDescription>
                        Connectez-vous pour accéder à votre planning
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
                                {error}
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="email">Email</Label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="votre@email.com"
                                    className="pl-10"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Mot de passe</Label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                                <Input
                                    id="password"
                                    type="password"
                                    placeholder="••••••••"
                                    className="pl-10"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <Button type="submit" className="w-full" disabled={isLoading}>
                            {isLoading ? "Connexion..." : "Se connecter"}
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}
