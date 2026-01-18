"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Trash2, Plus, Globe, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

interface Config {
    id: string;
    question: string;
    response: string;
    response_lang: string;
    created_at: string;
}

export default function CustomChatBotConfigPage() {
    const [configs, setConfigs] = useState<Config[]>([]);
    const [question, setQuestion] = useState("");
    const [response, setResponse] = useState("");
    const [responseLang, setResponseLang] = useState("fr");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadConfigs();
    }, []);

    const loadConfigs = async () => {
        try {
            const res = await api.get("/custom_chat_bot/config");
            setConfigs(res.data);
        } catch (e) {
            console.error("Failed to load configs:", e);
        }
    };

    const addConfig = async () => {
        if (!question.trim() || !response.trim()) return;

        setLoading(true);
        try {
            await api.post("/custom_chat_bot/config", {
                question,
                response,
                response_lang: responseLang
            });
            setQuestion("");
            setResponse("");
            setResponseLang("fr");
            loadConfigs();
        } catch (e) {
            console.error("Failed to add config:", e);
        } finally {
            setLoading(false);
        }
    };

    const deleteConfig = async (id: string) => {
        try {
            await api.delete(`/custom_chat_bot/config/${id}`);
            loadConfigs();
        } catch (e) {
            console.error("Failed to delete config:", e);
        }
    };

    const getLangLabel = (lang: string) => {
        const labels: Record<string, string> = {
            "fr": "🇫🇷 Français",
            "wo": "🇸🇳 Wolof",
            "en": "🇬🇧 English"
        };
        return labels[lang] || lang;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-8">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">
                            🤖 Custom ChatBot - Configuration
                        </h1>
                        <p className="text-slate-400">
                            Configurez les réponses prédéfinies pour votre chatbot
                        </p>
                    </div>
                    <Link href="/custom_chat_bot/test">
                        <Button className="bg-purple-600 hover:bg-purple-700">
                            Tester le ChatBot <ArrowRight className="ml-2 w-4 h-4" />
                        </Button>
                    </Link>
                </div>

                {/* Add Config Form */}
                <Card className="mb-8 bg-white/10 backdrop-blur border-white/20">
                    <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                            <Plus className="w-5 h-5" />
                            Ajouter une configuration Q&A
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-sm text-slate-300 mb-1 block">Question (mots-clés)</label>
                            <Input
                                placeholder="Ex: Comment vas-tu ?"
                                value={question}
                                onChange={(e) => setQuestion(e.target.value)}
                                className="bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                            />
                        </div>
                        <div>
                            <label className="text-sm text-slate-300 mb-1 block">Réponse</label>
                            <textarea
                                placeholder="Ex: Je vais très bien, merci de demander !"
                                value={response}
                                onChange={(e) => setResponse(e.target.value)}
                                className="w-full p-3 rounded-md bg-white/10 border border-white/20 text-white placeholder:text-slate-400 min-h-[100px]"
                            />
                        </div>
                        <div className="flex items-center gap-4">
                            <div className="flex-1">
                                <label className="text-sm text-slate-300 mb-1 block">Langue de la réponse</label>
                                <select
                                    value={responseLang}
                                    onChange={(e) => setResponseLang(e.target.value)}
                                    className="w-full p-3 rounded-md bg-white/10 border border-white/20 text-white"
                                >
                                    <option value="fr">🇫🇷 Français</option>
                                    <option value="wo">🇸🇳 Wolof</option>
                                    <option value="en">🇬🇧 English</option>
                                </select>
                            </div>
                            <Button
                                onClick={addConfig}
                                disabled={loading || !question.trim() || !response.trim()}
                                className="mt-6 bg-green-600 hover:bg-green-700"
                            >
                                {loading ? "..." : "Ajouter"}
                            </Button>
                        </div>
                    </CardContent>
                </Card>

                {/* Existing Configs */}
                <Card className="bg-white/10 backdrop-blur border-white/20">
                    <CardHeader>
                        <CardTitle className="text-white">Configurations existantes</CardTitle>
                        <CardDescription className="text-slate-400">
                            {configs.length} configuration(s)
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {configs.length === 0 ? (
                            <p className="text-slate-400 text-center py-8">
                                Aucune configuration. Ajoutez-en une pour commencer !
                            </p>
                        ) : (
                            <div className="space-y-3">
                                {configs.map((config) => (
                                    <div
                                        key={config.id}
                                        className="p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                                    >
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2 mb-2">
                                                    <span className="text-purple-400 font-medium">Q:</span>
                                                    <span className="text-white">{config.question}</span>
                                                </div>
                                                <div className="flex items-start gap-2">
                                                    <span className="text-green-400 font-medium">R:</span>
                                                    <span className="text-slate-300">{config.response}</span>
                                                </div>
                                                <div className="mt-2 flex items-center gap-2">
                                                    <Globe className="w-4 h-4 text-slate-400" />
                                                    <span className="text-xs text-slate-400">
                                                        {getLangLabel(config.response_lang)}
                                                    </span>
                                                </div>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => deleteConfig(config.id)}
                                                className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
