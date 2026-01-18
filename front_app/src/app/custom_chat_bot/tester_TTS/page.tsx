"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, Volume2, Loader2, Settings, ArrowLeft } from "lucide-react";
import api from "@/lib/api";
import Link from "next/link";

interface TTSCell {
    id: string;
    text: string;
    language: string;
    audioUrl: string | null;
    isLoading: boolean;
}

export default function TTSTesterPage() {
    const [cells, setCells] = useState<TTSCell[]>([
        { id: "1", text: "", language: "wo", audioUrl: null, isLoading: false }
    ]);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [playingId, setPlayingId] = useState<string | null>(null);

    const addCell = () => {
        setCells(prev => [
            ...prev,
            {
                id: Date.now().toString(),
                text: "",
                language: "wo",
                audioUrl: null,
                isLoading: false
            }
        ]);
    };

    const removeCell = (id: string) => {
        if (cells.length > 1) {
            setCells(prev => prev.filter(c => c.id !== id));
        }
    };

    const updateCell = (id: string, field: keyof TTSCell, value: string) => {
        setCells(prev => prev.map(c =>
            c.id === id ? { ...c, [field]: value, audioUrl: null } : c
        ));
    };

    const generateTTS = async (id: string) => {
        const cell = cells.find(c => c.id === id);
        if (!cell || !cell.text.trim()) return;

        setCells(prev => prev.map(c =>
            c.id === id ? { ...c, isLoading: true } : c
        ));

        try {
            const res = await api.post("/custom_chat_bot/tts", {
                text: cell.text,
                language: cell.language
            });

            // Get base URL (remove /api/v1 if present)
            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001/api/v1';
            const serverBase = apiBase.replace('/api/v1', '');
            const fullUrl = `${serverBase}${res.data.audio_url}`;

            setCells(prev => prev.map(c =>
                c.id === id ? { ...c, audioUrl: fullUrl, isLoading: false } : c
            ));
        } catch (e) {
            console.error("TTS generation failed:", e);
            setCells(prev => prev.map(c =>
                c.id === id ? { ...c, isLoading: false } : c
            ));
        }
    };

    const playAudio = (id: string, url: string) => {
        if (audioRef.current) {
            audioRef.current.src = url;
            audioRef.current.play().catch(console.error);
            setPlayingId(id);
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
                            🔊 TTS Tester
                        </h1>
                        <p className="text-slate-400">
                            Testez la synthèse vocale avec différentes langues
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Link href="/custom_chat_bot/conf">
                            <Button variant="outline" className="bg-transparent border-white/20 text-white hover:bg-white/10">
                                <Settings className="w-4 h-4 mr-2" /> Config
                            </Button>
                        </Link>
                        <Link href="/custom_chat_bot/test">
                            <Button variant="outline" className="bg-transparent border-white/20 text-white hover:bg-white/10">
                                <ArrowLeft className="w-4 h-4 mr-2" /> Chat Test
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Audio player (hidden) */}
                <audio
                    ref={audioRef}
                    className="hidden"
                    onEnded={() => setPlayingId(null)}
                />

                {/* Cells */}
                <div className="space-y-4">
                    {cells.map((cell, index) => (
                        <Card key={cell.id} className="bg-white/10 backdrop-blur border-white/20">
                            <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-white text-lg">
                                        Cell #{index + 1}
                                    </CardTitle>
                                    <div className="flex items-center gap-2">
                                        <select
                                            value={cell.language}
                                            onChange={(e) => updateCell(cell.id, "language", e.target.value)}
                                            className="px-3 py-1.5 rounded-md bg-white/10 border border-white/20 text-white text-sm"
                                        >
                                            <option value="wo">🇸🇳 Wolof</option>
                                            <option value="fr">🇫🇷 Français</option>
                                            <option value="en">🇬🇧 English</option>
                                        </select>
                                        {cells.length > 1 && (
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => removeCell(cell.id)}
                                                className="text-red-400 hover:text-red-300 hover:bg-red-500/20"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-3">
                                <textarea
                                    placeholder="Entrez le texte à synthétiser..."
                                    value={cell.text}
                                    onChange={(e) => updateCell(cell.id, "text", e.target.value)}
                                    className="w-full p-3 rounded-md bg-white/10 border border-white/20 text-white placeholder:text-slate-400 min-h-[100px] resize-none"
                                />
                                <div className="flex items-center gap-3">
                                    <Button
                                        onClick={() => generateTTS(cell.id)}
                                        disabled={cell.isLoading || !cell.text.trim()}
                                        className="bg-purple-600 hover:bg-purple-700"
                                    >
                                        {cell.isLoading ? (
                                            <>
                                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                                Génération...
                                            </>
                                        ) : (
                                            <>
                                                <Volume2 className="w-4 h-4 mr-2" />
                                                Générer TTS
                                            </>
                                        )}
                                    </Button>

                                    {cell.audioUrl && (
                                        <Button
                                            onClick={() => playAudio(cell.id, cell.audioUrl!)}
                                            variant="outline"
                                            className={`
                                                bg-transparent border-green-500/50 text-green-400 
                                                hover:bg-green-500/20 hover:text-green-300
                                                ${playingId === cell.id ? 'animate-pulse' : ''}
                                            `}
                                        >
                                            <Volume2 className="w-4 h-4 mr-2" />
                                            {playingId === cell.id ? "En lecture..." : "Écouter"}
                                        </Button>
                                    )}

                                    <span className="text-xs text-slate-400 ml-auto">
                                        {getLangLabel(cell.language)}
                                    </span>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>

                {/* Add Cell Button */}
                <div className="mt-6 flex justify-center">
                    <Button
                        onClick={addCell}
                        variant="outline"
                        className="bg-transparent border-dashed border-white/30 text-white hover:bg-white/10"
                    >
                        <Plus className="w-4 h-4 mr-2" />
                        Ajouter une cellule
                    </Button>
                </div>

                {/* Info */}
                <div className="mt-8 p-4 rounded-lg bg-white/5 border border-white/10">
                    <h3 className="text-white font-medium mb-2">ℹ️ Info</h3>
                    <ul className="text-sm text-slate-400 space-y-1">
                        <li>• <strong>Wolof</strong> : Utilise ADIA_TTS (ou xTTS si disponible)</li>
                        <li>• <strong>Français/Anglais</strong> : Utilise OpenAI TTS</li>
                        <li>• Le premier appel peut être lent (chargement des modèles)</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
