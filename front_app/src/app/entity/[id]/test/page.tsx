"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioPlayer } from "@/components/AudioPlayer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { History, Clock, Languages, Send, Bot, User as UserIcon, Sparkles } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { Message, Instance } from "@/types";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

// --- Types ---
interface Session {
    session_id: string;
    created_at: string;
    message_count: number;
    preview: string;
}

export default function TestChatbotPage() {
    const params = useParams();
    const entityId = params.id as string;

    // State
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [instances, setInstances] = useState<Instance[]>([]);
    const [selectedInstanceId, setSelectedInstanceId] = useState<string | null>(null);
    const [currentAudio, setCurrentAudio] = useState<string | null>(null);
    const [textInput, setTextInput] = useState("");
    const [selectedLanguage, setSelectedLanguage] = useState<string>("auto");
    const [sessionsList, setSessionsList] = useState<Session[]>([]);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Initial Fetch (Instances)
    useEffect(() => {
        const fetchInstances = async () => {
            try {
                const res = await api.get<Instance[]>("/instances");
                const entityInstances = (res.data || []).filter((i: Instance) => i.entity_id === entityId);
                setInstances(entityInstances);

                // Select first instance by default if none selected
                if (entityInstances.length > 0 && !selectedInstanceId) {
                    const defaultInstance = entityInstances[0];
                    setSelectedInstanceId(defaultInstance.instance_id);
                }
            } catch (e) {
                console.error("Error fetching instances", e);
            }
        };
        if (entityId) fetchInstances();
    }, [entityId]);

    // Session Management and Persistence
    useEffect(() => {
        if (!selectedInstanceId) return;

        // Try to recover session from localStorage
        const savedSessionKey = `session_${selectedInstanceId}`;
        const savedSessionId = localStorage.getItem(savedSessionKey);

        if (savedSessionId) {
            setSessionId(savedSessionId);
        } else {
            // Create new session automatically if none exists
            handleNewSession();
        }
    }, [selectedInstanceId]);

    // Fetch History when session changes
    useEffect(() => {
        if (!sessionId) return;
        const fetchHistory = async () => {
            try {
                const res = await api.get<Message[]>(`/sessions/${sessionId}/messages`);
                const formatted = (res.data || []).map((m: Message) => ({
                    ...m,
                    audio_path: m.audio_path && typeof m.audio_path === 'string' ? buildUploadsUrl(m.audio_path) : undefined
                }));
                setMessages(formatted);
            } catch (e) {
                console.error("Error fetching history", e);
                // If 404, maybe session invalid? Could clear local storage.
                if ((e as any).response?.status === 404) {
                    localStorage.removeItem(`session_${selectedInstanceId}`);
                    setSessionId(null);
                }
            }
        };
        fetchHistory();
    }, [sessionId]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, isProcessing]);

    // Helpers
    const buildUploadsUrl = (path?: string | null) => {
        if (!path) return undefined;
        if (path.startsWith("http")) return path;

        // Normalize path
        let cleanPath = path.replace(/\\/g, "/"); // windows -> unix
        const uploadsSegment = "/uploads/";
        const idx = cleanPath.lastIndexOf(uploadsSegment);
        if (idx !== -1) {
            cleanPath = cleanPath.substring(idx + 1);
        } else {
            const parts = cleanPath.split("/");
            const filename = parts[parts.length - 1];
            cleanPath = `uploads/${filename}`;
        }
        cleanPath = cleanPath.replace(/^\/+/, "");

        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace("/api/v1", "") || "http://localhost:9000";
        return `${baseUrl}/${cleanPath}`;
    };

    const addMessage = (msg: Message) => {
        setMessages(prev => [...prev, msg]);
    };

    const updateLastUserMessage = (transcription: string, audioUrl?: string | null) => {
        setMessages(prev => {
            const newMsgs = [...prev];
            // Search backwards for the last user message
            for (let i = newMsgs.length - 1; i >= 0; i--) {
                if (newMsgs[i].role === 'user') {
                    newMsgs[i] = {
                        ...newMsgs[i],
                        content: transcription,
                        audio_path: audioUrl ? buildUploadsUrl(audioUrl) : newMsgs[i].audio_path
                    } as Message;
                    break;
                }
            }
            return newMsgs;
        });
    };

    const handleNewSession = async () => {
        if (!selectedInstanceId) return;
        try {
            const res = await api.post("/chat/sessions", { instance_id: selectedInstanceId });
            if (res.data.success) {
                const newSessionId = res.data.session_id;
                setSessionId(newSessionId);
                setMessages([]); // Clear messages for new session
                // Save to localStorage
                localStorage.setItem(`session_${selectedInstanceId}`, newSessionId);
            }
        } catch (e) {
            console.error("Error creating new session", e);
        }
    };

    const fetchSessions = async () => {
        if (!selectedInstanceId) return;
        try {
            const res = await api.get(`/chat/sessions?instance_id=${selectedInstanceId}`);
            setSessionsList(res.data);
        } catch (e) {
            console.error("Error fetching sessions", e);
        }
    };

    const handleSessionSelect = (sid: string) => {
        setSessionId(sid);
        localStorage.setItem(`session_${selectedInstanceId}`, sid);
        setIsHistoryOpen(false);
    };

    const handleInstanceChange = (value: string) => {
        setSelectedInstanceId(value);
        setSessionId(null); // Reset session until loaded/created for new instance
        setMessages([]);
    };

    // Handlers
    const handleSendText = async () => {
        const text = textInput.trim();
        if (!text || !selectedInstanceId) return;

        setIsProcessing(true);
        setTextInput("");

        // Optimistic UI
        const tempMsg: Message = {
            message_id: `temp-${Date.now()}`,
            session_id: sessionId || "temp",
            instance_id: selectedInstanceId,
            role: "user",
            content: text,
            created_at: new Date().toISOString()
        };
        addMessage(tempMsg);

        try {
            const res = await api.post("/chat/text", {
                instance_id: selectedInstanceId,
                text,
                forced_language: selectedLanguage !== "auto" ? selectedLanguage : null,
                session_id: sessionId // Pass current session ID
            });
            const data = res.data;

            if (data.session_id && sessionId !== data.session_id) {
                setSessionId(data.session_id);
                localStorage.setItem(`session_${selectedInstanceId}`, data.session_id);
            }

            const botMsg: Message = {
                message_id: `bot-${Date.now()}`,
                session_id: data.session_id,
                instance_id: selectedInstanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString()
            };
            addMessage(botMsg);

            if (data.response_audio) {
                setCurrentAudio(buildUploadsUrl(data.response_audio) ?? null);
            }

        } catch (error) {
            console.error("Error sending message:", error);
            addMessage({
                message_id: `err-${Date.now()}`,
                role: "system",
                content: "Erreur de connexion.",
                session_id: "err",
                instance_id: selectedInstanceId || "unknown",
                created_at: new Date().toISOString()
            });
        } finally {
            setIsProcessing(false);
            // Re-focus input
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    // Voice Handler
    const handleVoiceRecordingComplete = async (blob: Blob) => {
        if (!selectedInstanceId) return;

        setIsProcessing(true);

        // Optimistic UI (placeholder)
        const tempMsg: Message = {
            message_id: `temp-${Date.now()}`,
            session_id: sessionId || "temp",
            instance_id: selectedInstanceId,
            role: "user",
            content: "🎤 Message vocal...",
            created_at: new Date().toISOString()
        };
        addMessage(tempMsg);

        const formData = new FormData();
        formData.append("audio_file", blob, "recording.webm");
        formData.append("instance_id", selectedInstanceId);
        if (selectedLanguage !== "auto") {
            formData.append("forced_language", selectedLanguage);
        }
        if (sessionId) {
            formData.append("session_id", sessionId);
        }

        try {
            const res = await api.post("/chat/messages", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            const data = res.data;

            if (data.session_id && sessionId !== data.session_id) {
                setSessionId(data.session_id);
                localStorage.setItem(`session_${selectedInstanceId}`, data.session_id);
            }

            // Update user message with real transcription
            updateLastUserMessage(data.transcription, data.user_audio);

            const botMsg: Message = {
                message_id: `bot-${Date.now()}`,
                session_id: data.session_id,
                instance_id: selectedInstanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString()
            };
            addMessage(botMsg);

            // Auto play audio
            if (botMsg.audio_path) {
                setCurrentAudio(botMsg.audio_path);
            }

        } catch (error) {
            console.error("Voice error", error);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex h-screen flex-col bg-slate-50">
            {/* Header */}
            <header className="border-b bg-white px-6 py-4 flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-2">
                        <Avatar className="h-8 w-8">
                            <AvatarFallback className="bg-indigo-100 text-indigo-600">
                                <Bot className="h-5 w-5" />
                            </AvatarFallback>
                        </Avatar>
                        <h1 className="text-xl font-semibold text-slate-800">
                            Test du Chatbot
                        </h1>
                    </div>
                    <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                        <Sparkles className="h-3 w-3 text-amber-400" />
                        En ligne • OpenAI Powered
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    {/* History Button (Sheet) */}
                    <Sheet open={isHistoryOpen} onOpenChange={setIsHistoryOpen}>
                        <SheetTrigger asChild>
                            <Button
                                variant="outline"
                                size="sm"
                                className="gap-2"
                                disabled={!selectedInstanceId}
                                onClick={fetchSessions}
                            >
                                <History className="h-4 w-4" />
                                Historique
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="right">
                            <SheetHeader>
                                <SheetTitle>Conversations récentes</SheetTitle>
                            </SheetHeader>
                            <ScrollArea className="h-[calc(100vh-100px)] mt-4">
                                <div className="space-y-2 pr-4">
                                    {sessionsList.length === 0 ? (
                                        <p className="text-sm text-slate-500 text-center py-4">
                                            Aucune conversation trouvée.
                                        </p>
                                    ) : (
                                        sessionsList.map((sess) => (
                                            <div
                                                key={sess.session_id}
                                                onClick={() => handleSessionSelect(sess.session_id)}
                                                className={cn(
                                                    "cursor-pointer rounded-lg p-3 border transition-colors hover:bg-slate-50",
                                                    sessionId === sess.session_id ? "border-indigo-500 bg-indigo-50/50 ring-1 ring-indigo-500" : "border-slate-200 bg-white"
                                                )}
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                    <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        {new Date(sess.created_at).toLocaleDateString("fr-FR", {
                                                            day: "2-digit",
                                                            month: "short",
                                                            hour: "2-digit",
                                                            minute: "2-digit",
                                                        })}
                                                    </span>
                                                    <span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                                                        {sess.message_count} msg
                                                    </span>
                                                </div>
                                                <p className="text-sm text-slate-700 line-clamp-2">
                                                    {sess.preview}
                                                </p>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </ScrollArea>
                        </SheetContent>
                    </Sheet>

                    {/* Instance Selector */}
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-700">Instance:</span>
                        <Select value={selectedInstanceId || ""} onValueChange={handleInstanceChange}>
                            <SelectTrigger className="w-[180px]">
                                <SelectValue placeholder="Choisir..." />
                            </SelectTrigger>
                            <SelectContent>
                                {instances.map((inst) => (
                                    <SelectItem key={inst.instance_id} value={inst.instance_id}>
                                        {inst.name}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Language Selector */}
                    <div className="flex items-center gap-2">
                        <Languages className="h-4 w-4 text-slate-500" />
                        <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                            <SelectTrigger className="w-[100px]">
                                <SelectValue placeholder="Langue" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Auto</SelectItem>
                                <SelectItem value="wolof">Wolof</SelectItem>
                                <SelectItem value="fr">Français</SelectItem>
                                <SelectItem value="en">English</SelectItem>
                                <SelectItem value="ar">Arabic</SelectItem>
                                <SelectItem value="es">Spanish</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <Button
                        variant="default"
                        size="sm"
                        onClick={handleNewSession}
                        disabled={!selectedInstanceId}
                    >
                        <Sparkles className="h-4 w-4 mr-2" />
                        Nouveau
                    </Button>
                </div>
            </header>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-6" ref={scrollRef}>
                <div className="mx-auto max-w-3xl space-y-6">
                    {messages.length === 0 && (
                        <div className="flex h-[300px] flex-col items-center justify-center text-center opacity-70 animate-in fade-in zoom-in duration-500">
                            <div className="rounded-full bg-indigo-100 p-6 mb-4">
                                <Sparkles className="h-12 w-12 text-indigo-500" />
                            </div>
                            <h3 className="text-lg font-semibold text-slate-700">Bonjour !</h3>
                            <p className="max-w-xs text-sm text-slate-500 mt-1">
                                Je suis l'assistant virtuel de l'Hôpital Fann. Posez-moi une question ou prenez rendez-vous.
                            </p>
                        </div>
                    )}

                    {messages.map((msg, idx) => {
                        const isUser = msg.role === 'user';
                        const isSystem = msg.role === 'system';
                        return (
                            <div
                                key={msg.message_id || idx}
                                className={cn(
                                    "flex w-full animate-in fade-in slide-in-from-bottom-2 duration-300",
                                    isUser ? "justify-end" : "justify-start"
                                )}
                            >
                                <div className={cn(
                                    "flex max-w-[85%] gap-3 md:max-w-[75%]",
                                    isUser ? "flex-row-reverse" : "flex-row"
                                )}>
                                    {/* Avatar Bubble */}
                                    <Avatar className={cn("h-8 w-8 mt-1 shadow-sm", isSystem && "hidden")}>
                                        <AvatarFallback className={cn(
                                            "text-xs",
                                            isUser ? "bg-indigo-600 text-white" : "bg-white border border-slate-200 text-indigo-600"
                                        )}>
                                            {isUser ? <UserIcon className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                        </AvatarFallback>
                                    </Avatar>

                                    {/* Message Bubble */}
                                    <div className={cn(
                                        "group relative rounded-2xl px-5 py-3 shadow-sm text-sm leading-relaxed",
                                        isUser
                                            ? "bg-indigo-600 text-white rounded-tr-none"
                                            : isSystem
                                                ? "bg-red-50 text-red-600 border border-red-100 w-full text-center italic"
                                                : "bg-white border border-white/50 text-slate-700 rounded-tl-none shadow-md"
                                    )}>
                                        <p className="whitespace-pre-wrap">{msg.content}</p>

                                        {/* Audio Player in Bubble */}
                                        {msg.audio_path && (
                                            <div className={cn(
                                                "mt-3 rounded-xl p-2",
                                                isUser ? "bg-indigo-700/50" : "bg-slate-50"
                                            )}>
                                                <AudioPlayer src={msg.audio_path} />
                                            </div>
                                        )}

                                        <div className={cn(
                                            "absolute bottom-1 text-[10px] opacity-0 transition-opacity group-hover:opacity-100",
                                            isUser ? "left-2 text-indigo-200" : "right-2 text-slate-400"
                                        )}>
                                            {new Date(msg.created_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        );
                    })}

                    {isProcessing && (
                        <div className="flex w-full justify-start animate-in fade-in">
                            <div className="flex items-center gap-3">
                                <Avatar className="h-8 w-8 bg-white border border-slate-100">
                                    <AvatarFallback><Bot className="h-4 w-4 text-indigo-500" /></AvatarFallback>
                                </Avatar>
                                <div className="flex items-center space-x-1 rounded-2xl rounded-tl-none bg-white px-4 py-3 shadow-sm border border-slate-100">
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.3s]"></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400 [animation-delay:-0.15s]"></div>
                                    <div className="h-2 w-2 animate-bounce rounded-full bg-indigo-400"></div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Global Audio Auto-Play (Hidden or Bottom) */}
            {
                currentAudio && (
                    <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 animate-in slide-in-from-bottom-5 fade-in">
                        <div className="flex items-center gap-3 rounded-full bg-black/80 px-4 py-2 text-white shadow-2xl backdrop-blur-md">
                            <span className="text-xs font-medium animate-pulse">Lecture en cours...</span>
                            <AudioPlayer src={currentAudio} autoPlay />
                        </div>
                    </div>
                )
            }

            {/* Input Bar */}
            <div className="border-t border-white/50 bg-white/80 p-4 backdrop-blur-md">
                <div className="mx-auto flex max-w-3xl flex-col gap-3">
                    {/* Language Selector Row */}
                    <div className="flex items-center gap-2 mb-1">
                        <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500 bg-slate-100/50 px-2 py-1 rounded-md border border-slate-200/50">
                            <Languages className="h-3.5 w-3.5" />
                            <span>Langue :</span>
                        </div>
                        <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                            <SelectTrigger className="h-8 w-[140px] text-xs bg-white/80 border-slate-200">
                                <SelectValue placeholder="Choisis une langue" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="auto">Détection Auto</SelectItem>
                                <SelectItem value="wolof">Wolof</SelectItem>
                                <SelectItem value="fr">Français</SelectItem>
                                <SelectItem value="en">Anglais</SelectItem>
                                <SelectItem value="ar">Arabe</SelectItem>
                                <SelectItem value="es">Espagnol</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="relative flex-1">
                            <Input
                                ref={inputRef}
                                value={textInput}
                                onChange={(e) => setTextInput(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
                                placeholder="Écrivez votre message..."
                                className="pr-12 h-12 rounded-full border-slate-200 bg-white pl-5 shadow-sm focus-visible:ring-indigo-500"
                                disabled={!selectedInstanceId || isProcessing}
                            />
                            {/* Send Button inside Input if text exists */}
                            {textInput.trim() && (
                                <Button
                                    size="icon"
                                    onClick={handleSendText}
                                    disabled={isProcessing}
                                    className="absolute right-1 top-1 h-10 w-10 rounded-full bg-indigo-600 hover:bg-indigo-700 transition-all animate-in zoom-in"
                                >
                                    <Send className="h-4 w-4 text-white" />
                                </Button>
                            )}
                        </div>
                        <AudioRecorder
                            onRecordingComplete={handleVoiceRecordingComplete}
                            isProcessing={isProcessing}
                            disabled={!selectedInstanceId}
                        />
                    </div>
                </div>
            </div>
            <div className="mt-2 text-center text-[10px] text-slate-400">
                TonToumaBot v1.0 • Propulsé par OpenAI
            </div>
        </div>
    );
}
