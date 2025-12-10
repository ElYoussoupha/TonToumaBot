"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioPlayer } from "@/components/AudioPlayer";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Send, Bot, User as UserIcon, Loader2, Sparkles, MoreHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import { Message, Instance } from "@/types";

// --- Types ---
interface ChatState {
    messages: Message[];
    isProcessing: boolean;
    sessionId: string | null;
    instanceId: string | null;
    currentAudio: string | null;
}

export default function TestChatbotPage() {
    const params = useParams();
    const entityId = params.id as string;

    // State
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [instanceId, setInstanceId] = useState<string | null>(null);
    const [currentAudio, setCurrentAudio] = useState<string | null>(null);
    const [textInput, setTextInput] = useState("");

    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Initial Fetch (Instance)
    useEffect(() => {
        const fetchInstance = async () => {
            try {
                const res = await api.get<Instance[]>("/instances");
                const target = (res.data || []).find((i: Instance) => i.entity_id === entityId);
                if (target) setInstanceId(target.instance_id);
            } catch (e) {
                console.error("Error fetching instances", e);
            }
        };
        if (entityId) fetchInstance();
    }, [entityId]);

    // Fetch History
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
        if (!path) return null;
        if (path.startsWith("http")) return path;

        // Normaliser le chemin pour gérer :
        // - chemins système du backend (/app/uploads/xxx.mp3)
        // - chemins déjà publics (/uploads/xxx.mp3 ou uploads/xxx.mp3)
        // - simples noms de fichiers (xxx.mp3)
        let cleanPath = path.replace(/\\/g, "/"); // windows -> unix

        const uploadsSegment = "/uploads/";
        const idx = cleanPath.lastIndexOf(uploadsSegment);
        if (idx !== -1) {
            // Garder à partir de "uploads/xxx.mp3"
            cleanPath = cleanPath.substring(idx + 1); // enlève le premier '/'
        } else {
            // Pas de segment /uploads/, on reconstruit à partir du nom de fichier
            const parts = cleanPath.split("/");
            const filename = parts[parts.length - 1];
            cleanPath = `uploads/${filename}`;
        }

        // S'assurer qu'il n'y a pas de slash de tête pour la concaténation
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
            const lastIdx = newMsgs.length - 1;
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

    // Handlers
    const handleSendText = async () => {
        const text = textInput.trim();
        if (!text || !instanceId) return;

        setIsProcessing(true);
        setTextInput("");

        // Optimistic UI
        const tempMsg: Message = {
            message_id: `temp-${Date.now()}`,
            session_id: sessionId || "temp",
            instance_id: instanceId,
            role: "user",
            content: text,
            created_at: new Date().toISOString()
        };
        addMessage(tempMsg);

        try {
            const res = await api.post("/chat/text", { instance_id: instanceId, text });
            const data = res.data;

            if (data.session_id && !sessionId) setSessionId(data.session_id);

            const botMsg: Message = {
                message_id: `bot-${Date.now()}`,
                session_id: data.session_id,
                instance_id: instanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString()
            };
            addMessage(botMsg);

            if (data.response_audio) {
                setCurrentAudio(buildUploadsUrl(data.response_audio));
            }

        } catch (e) {
            console.error(e);
            addMessage({
                message_id: `err-${Date.now()}`,
                role: "system",
                content: "Erreur de connexion.",
                session_id: "err",
                instance_id: instanceId,
                created_at: new Date().toISOString()
            });
        } finally {
            setIsProcessing(false);
            // Re-focus input
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    };

    const handleAudioRecord = async (blob: Blob) => {
        if (!instanceId) return;
        setIsProcessing(true);
        setCurrentAudio(null);

        // Optimistic
        addMessage({
            message_id: `temp-audio-${Date.now()}`,
            session_id: sessionId || "temp",
            instance_id: instanceId,
            role: "user",
            content: "🎤 Analyse audio en cours...",
            created_at: new Date().toISOString()
        });

        const formData = new FormData();
        formData.append("audio_file", blob, "rec.wav");
        formData.append("instance_id", instanceId);

        try {
            const res = await api.post("/chat/messages", formData);
            const data = res.data;

            if (data.session_id && !sessionId) setSessionId(data.session_id);

            // Update user msg with transcription
            updateLastUserMessage(data.transcription, data.user_audio);

            // Add Bot response
            const botMsg: Message = {
                message_id: `bot-${Date.now()}`,
                session_id: data.session_id,
                instance_id: instanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString()
            };
            addMessage(botMsg);

            if (data.response_audio) {
                setCurrentAudio(buildUploadsUrl(data.response_audio));
            }

        } catch (e) {
            console.error(e);
            addMessage({
                message_id: `err-${Date.now()}`,
                role: "system",
                content: "Erreur lors du traitement audio.",
                session_id: "err",
                instance_id: instanceId,
                created_at: new Date().toISOString()
            });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="relative flex h-[calc(100vh-1rem)] w-full flex-col overflow-hidden bg-gradient-to-br from-indigo-50 via-white to-purple-50 rounded-2xl shadow-2xl border border-slate-200">

            {/* Header */}
            <header className="flex items-center justify-between border-b border-white/50 bg-white/60 px-6 py-4 backdrop-blur-md z-10">
                <div className="flex items-center gap-3">
                    <div className="relative">
                        <Avatar className="h-10 w-10 border-2 border-indigo-100 shadow-sm">
                            <AvatarImage src="/bot-avatar.png" />
                            <AvatarFallback className="bg-gradient-to-br from-indigo-500 to-purple-600 text-white">
                                <Bot className="h-5 w-5" />
                            </AvatarFallback>
                        </Avatar>
                        <span className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-green-500 border-2 border-white ring-1 ring-green-100"></span>
                    </div>
                    <div>
                        <h1 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                            Assistant Fann
                            <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-[10px] font-semibold text-indigo-700 uppercase tracking-wider">
                                IA
                            </span>
                        </h1>
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                            <Sparkles className="h-3 w-3 text-amber-400" />
                            En ligne • OpenAI Powered
                        </p>
                    </div>
                </div>
                <Button variant="ghost" size="icon" className="text-slate-400 hover:text-slate-600">
                    <MoreHorizontal className="h-5 w-5" />
                </Button>
            </header>

            {/* Chat Area */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto px-4 py-6 scroll-smooth"
            >
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
            {currentAudio && (
                <div className="absolute bottom-20 left-1/2 -translate-x-1/2 z-20 animate-in slide-in-from-bottom-5 fade-in">
                    <div className="flex items-center gap-3 rounded-full bg-black/80 px-4 py-2 text-white shadow-2xl backdrop-blur-md">
                        <span className="text-xs font-medium animate-pulse">Lecture en cours...</span>
                        <AudioPlayer src={currentAudio} autoPlay />
                    </div>
                </div>
            )}

            {/* Input Bar */}
            <div className="border-t border-white/50 bg-white/80 p-4 backdrop-blur-md">
                <div className="mx-auto flex max-w-3xl items-center gap-3">
                    <div className="relative flex-1">
                        <Input
                            ref={inputRef}
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendText()}
                            placeholder="Écrivez votre message..."
                            className="pr-12 h-12 rounded-full border-slate-200 bg-white pl-5 shadow-sm focus-visible:ring-indigo-500"
                            disabled={!instanceId || isProcessing}
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

                    {/* Audio Recorder Button (Standalone if no text) */}
                    {!textInput.trim() && (
                        <AudioRecorder
                            onRecordingComplete={handleAudioRecord}
                            isProcessing={isProcessing}
                            disabled={!instanceId}
                        />
                    )}
                </div>
                <div className="mt-2 text-center text-[10px] text-slate-400">
                    TonToumaBot v1.0 • Propulsé par OpenAI
                </div>
            </div>
        </div>
    );
}
