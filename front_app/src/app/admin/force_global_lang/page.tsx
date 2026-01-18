"use client";

import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { Globe, Loader2, Check } from "lucide-react";

interface LanguageOption {
    code: string;
    name: string;
    flag: string;
}

const LANGUAGES: LanguageOption[] = [
    { code: "none", name: "Détection Auto", flag: "🔄" },
    { code: "wo", name: "Wolof", flag: "🇸🇳" },
    { code: "fr", name: "Français", flag: "🇫🇷" },
    { code: "en", name: "English", flag: "🇬🇧" },
    { code: "ar", name: "العربية", flag: "🇸🇦" },
];

export default function ForceGlobalLangPage() {
    const [selectedLang, setSelectedLang] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        const fetchCurrentLang = async () => {
            try {
                const res = await api.get("/settings/global_language");
                setSelectedLang(res.data.forced_language || "none");
            } catch (e) {
                console.error("Failed to fetch global language", e);
                setSelectedLang("none");
            } finally {
                setIsLoading(false);
            }
        };
        fetchCurrentLang();
    }, []);

    const handleSelectLanguage = async (langCode: string) => {
        if (langCode === selectedLang || isSaving) return;

        setIsSaving(true);
        try {
            await api.post("/settings/global_language", { language: langCode });
            setSelectedLang(langCode);
        } catch (e) {
            console.error("Failed to set global language", e);
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 p-6">
            <div className="mx-auto max-w-lg">
                {/* Header */}
                <div className="mb-8 text-center">
                    <div className="inline-flex items-center justify-center rounded-full bg-indigo-100 p-3 mb-4">
                        <Globe className="h-6 w-6 text-indigo-600" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800">Langue Globale</h1>
                    <p className="text-sm text-slate-500 mt-1">
                        Force la langue pour toutes les requêtes
                    </p>
                </div>

                {/* Language Options - Radio Style */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    {LANGUAGES.map((lang, idx) => {
                        const isSelected = selectedLang === lang.code;
                        const isLast = idx === LANGUAGES.length - 1;

                        return (
                            <button
                                key={lang.code}
                                onClick={() => handleSelectLanguage(lang.code)}
                                disabled={isSaving}
                                className={cn(
                                    "w-full flex items-center justify-between px-4 py-3.5 transition-colors",
                                    "hover:bg-slate-50 focus:outline-none focus:bg-slate-50",
                                    !isLast && "border-b border-slate-100",
                                    isSaving && "opacity-50 cursor-not-allowed"
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <span className="text-xl">{lang.flag}</span>
                                    <span className={cn(
                                        "font-medium",
                                        isSelected ? "text-indigo-600" : "text-slate-700"
                                    )}>
                                        {lang.name}
                                    </span>
                                </div>

                                {/* Radio/Switch indicator */}
                                <div className={cn(
                                    "w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all",
                                    isSelected
                                        ? "border-indigo-600 bg-indigo-600"
                                        : "border-slate-300 bg-white"
                                )}>
                                    {isSelected && (
                                        <Check className="h-3 w-3 text-white" />
                                    )}
                                </div>
                            </button>
                        );
                    })}
                </div>

                {/* Status indicator */}
                <div className="mt-6 text-center">
                    <div className={cn(
                        "inline-flex items-center gap-2 text-sm px-3 py-1.5 rounded-full",
                        selectedLang === "none"
                            ? "bg-slate-100 text-slate-600"
                            : "bg-indigo-50 text-indigo-700"
                    )}>
                        {isSaving ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        ) : (
                            <span className="text-base">
                                {LANGUAGES.find(l => l.code === selectedLang)?.flag}
                            </span>
                        )}
                        <span>
                            {selectedLang === "none"
                                ? "Mode automatique actif"
                                : `Forcé: ${LANGUAGES.find(l => l.code === selectedLang)?.name}`
                            }
                        </span>
                    </div>
                </div>

                {/* Info */}
                <p className="text-xs text-slate-400 text-center mt-4">
                    Les requêtes avec <code className="bg-slate-100 px-1 rounded">forced_language</code> ont priorité.
                </p>
            </div>
        </div>
    );
}
