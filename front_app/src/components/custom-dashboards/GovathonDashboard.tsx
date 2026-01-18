"use client";

import { useState, useEffect } from "react";
import {
    Trophy,
    Users,
    FileText,
    Calendar,
    MapPin,
    Clock,
    TrendingUp,
    Zap,
    ExternalLink,
    MessageSquare,
    Award,
    Star
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Entity } from "@/types";

interface GovathonDashboardProps {
    entityId: string;
    entity: Entity;
}

// Top 10 projects from the leaderboard
const TOP_PROJECTS = [
    { rank: 1, name: "i-Ticket", team: "Art'Beau-Rescence", type: "Startup", votes: 4781 },
    { rank: 2, name: "TONTOUMA BOT", team: "TONTOUMA BOT", type: "ESP", votes: 4717, highlight: true },
    { rank: 3, name: "SEN DON", team: "Wa Daraji", type: "UIDT", votes: 4156 },
    { rank: 4, name: "Sotilma", team: "SOTILMA", type: "Startup", votes: 3717 },
    { rank: 5, name: "SunuMarket", team: "SunuMarket", type: "EPT", votes: 2984 },
    { rank: 6, name: "Kay Bay", team: "Elite", type: "ISM", votes: 2378 },
    { rank: 7, name: "KaaySigné", team: "Le Patriotes", type: "Startup", votes: 2255 },
    { rank: 8, name: "Kaaraange", team: "KAARAANGE", type: "UADB", votes: 2109 },
    { rank: 9, name: "eSanté Enfant", team: "les isepiennes", type: "ISEP-AT", votes: 1962 },
    { rank: 10, name: "EKOLO", team: "InnovatorFutur", type: "ISI", votes: 1643 },
];

const STATS = {
    totalProjects: 812,
    finalists: 104,
    studentProjects: 72,
    startups: 11,
    citizenProjects: 21
};

export default function GovathonDashboard({ entityId, entity }: GovathonDashboardProps) {

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 p-6 -m-8">
            {/* Hero Section */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-500 p-8 mb-8 shadow-2xl">
                <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNjB2NjBIMHoiLz48cGF0aCBkPSJNMzAgMzBtLTI4IDBhMjggMjggMCAxIDAgNTYgMCAyOCAyOCAwIDEgMC01NiAwIiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC4xKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9nPjwvc3ZnPg==')] opacity-30" />
                <div className="relative z-10">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                        <div>
                            <Badge className="bg-white/20 text-white border-0 mb-4">
                                🇸🇳 2ème Édition
                            </Badge>
                            <h1 className="text-4xl md:text-5xl font-black text-white mb-2 tracking-tight">
                                GOV'ATHON 2025
                            </h1>
                            <p className="text-xl text-white/90 font-medium">
                                Hackathon Gouvernemental du Sénégal
                            </p>
                            <div className="flex items-center gap-2 mt-4 text-white/80">
                                <MapPin className="h-4 w-4" />
                                <span>CICAD Diamniadio</span>
                                <span className="mx-2">•</span>
                                <Calendar className="h-4 w-4" />
                                <span>23 Décembre 2025</span>
                            </div>
                        </div>

                        {/* Live Event Banner */}
                        <div className="text-center">
                            <div className="bg-white/20 backdrop-blur rounded-2xl p-6">
                                <Zap className="h-12 w-12 text-yellow-300 mx-auto mb-2 animate-pulse" />
                                <p className="text-2xl font-bold text-white">C'EST LE JOUR J !</p>
                                <p className="text-white/80">La finale a lieu maintenant</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {[
                    { icon: FileText, label: "Projets soumis", value: STATS.totalProjects, color: "from-blue-500 to-cyan-500" },
                    { icon: Trophy, label: "Finalistes", value: STATS.finalists, color: "from-amber-500 to-orange-500" },
                    { icon: Users, label: "Projets étudiants", value: STATS.studentProjects, color: "from-purple-500 to-pink-500" },
                ].map((stat, i) => (
                    <Card key={i} className="bg-slate-800/60 border-slate-700 backdrop-blur overflow-hidden">
                        <div className={`h-1 bg-gradient-to-r ${stat.color}`} />
                        <CardContent className="pt-4">
                            <div className="flex items-center gap-3">
                                <div className={`p-2 rounded-lg bg-gradient-to-br ${stat.color}`}>
                                    <stat.icon className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="text-xs text-slate-400">{stat.label}</p>
                                    <p className="text-xl font-bold text-white">{stat.value}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid md:grid-cols-3 gap-6">
                {/* Leaderboard */}
                <div className="md:col-span-2">
                    <Card className="bg-slate-800/60 border-slate-700 backdrop-blur">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between">
                                <CardTitle className="text-white flex items-center gap-2">
                                    <TrendingUp className="h-5 w-5 text-emerald-400" />
                                    Classement des Votes
                                </CardTitle>
                                <Badge variant="outline" className="border-emerald-500/50 text-emerald-400">
                                    Top 10
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-2">
                                {TOP_PROJECTS.map((project) => (
                                    <div
                                        key={project.rank}
                                        className={`flex items-center gap-4 p-3 rounded-xl transition-all ${project.highlight
                                            ? "bg-gradient-to-r from-emerald-600/30 to-teal-600/30 border border-emerald-500/50"
                                            : "bg-slate-700/40 hover:bg-slate-700/60"
                                            }`}
                                    >
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${project.rank === 1 ? "bg-yellow-500 text-yellow-950" :
                                            project.rank === 2 ? "bg-slate-300 text-slate-800" :
                                                project.rank === 3 ? "bg-amber-600 text-amber-100" :
                                                    "bg-slate-600 text-slate-300"
                                            }`}>
                                            {project.rank}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className={`font-semibold truncate ${project.highlight ? "text-emerald-300" : "text-white"}`}>
                                                {project.name}
                                                {project.highlight && <Star className="inline h-4 w-4 ml-1 text-yellow-400" />}
                                            </p>
                                            <p className="text-xs text-slate-400 truncate">
                                                {project.team} • {project.type}
                                            </p>
                                        </div>
                                        <div className="text-right">
                                            <p className={`font-bold ${project.highlight ? "text-emerald-400" : "text-white"}`}>
                                                {project.votes.toLocaleString()}
                                            </p>
                                            <p className="text-xs text-slate-500">votes</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <a
                                href="https://vote.govathon.sn/classement"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="mt-4 flex items-center justify-center gap-2 text-sm text-emerald-400 hover:text-emerald-300 transition-colors"
                            >
                                Voir le classement complet <ExternalLink className="h-4 w-4" />
                            </a>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column */}
                <div className="space-y-6">
                    {/* Quick Actions */}
                    <Card className="bg-slate-800/60 border-slate-700 backdrop-blur">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-white text-lg">Actions Rapides</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            <Button
                                className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg"
                                onClick={() => window.location.href = `/entity/${entityId}/test`}
                            >
                                <MessageSquare className="mr-2 h-4 w-4" />
                                Tester le Chatbot
                            </Button>
                            <Button
                                variant="outline"
                                className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
                                onClick={() => window.location.href = `/entity/${entityId}/knowledge`}
                            >
                                <FileText className="mr-2 h-4 w-4" />
                                Base de Connaissances
                            </Button>
                            <Button
                                variant="outline"
                                className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
                                onClick={() => window.open("https://reservation.govathon.sn", "_blank")}
                            >
                                <Calendar className="mr-2 h-4 w-4" />
                                Réserver une Place
                            </Button>
                        </CardContent>
                    </Card>

                    {/* Event Info */}
                    <Card className="bg-gradient-to-br from-amber-900/40 to-orange-900/40 border-amber-700/50 backdrop-blur">
                        <CardContent className="pt-6">
                            <div className="text-center">
                                <Award className="h-12 w-12 text-amber-400 mx-auto mb-3" />
                                <h3 className="text-lg font-bold text-white mb-1">Grande Finale</h3>
                                <p className="text-amber-200/80 text-sm">23 Décembre 2025 à 10h</p>
                                <p className="text-amber-200/60 text-xs mt-2">
                                    CICAD Diamniadio, Dakar
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Categories Distribution */}
                    <Card className="bg-slate-800/60 border-slate-700 backdrop-blur">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-white text-lg">Répartition Finalistes</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-3">
                                {[
                                    { label: "Étudiants", count: 72, color: "bg-blue-500", pct: 69 },
                                    { label: "Citoyens", count: 21, color: "bg-purple-500", pct: 20 },
                                    { label: "Startups", count: 11, color: "bg-amber-500", pct: 11 },
                                ].map((cat, i) => (
                                    <div key={i}>
                                        <div className="flex justify-between text-sm mb-1">
                                            <span className="text-slate-300">{cat.label}</span>
                                            <span className="text-white font-medium">{cat.count}</span>
                                        </div>
                                        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                            <div
                                                className={`h-full ${cat.color} rounded-full transition-all`}
                                                style={{ width: `${cat.pct}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Footer */}
            <div className="mt-8 text-center">
                <p className="text-slate-500 text-sm">
                    Chatbot propulsé par <span className="text-emerald-500 font-medium">TONTOUMA BOT</span> •
                    <a href="https://govathon.sn" target="_blank" rel="noopener noreferrer" className="ml-1 text-slate-400 hover:text-white transition-colors">
                        govathon.sn
                    </a>
                </p>
            </div>
        </div>
    );
}
