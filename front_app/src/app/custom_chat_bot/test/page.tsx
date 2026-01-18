"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Send, Bot, User as UserIcon, Loader2, Settings, Trash2, Volume2 } from "lucide-react";
import { cn } from "@/lib/utils";
import api from "@/lib/api";
import Link from "next/link";

interface Message {
    id: string;
    session_id: string;
    role: string;
    content: string;
    audio_url: string | null;
    created_at: string;
}

export default function CustomChatBotTestPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [sessionId] = useState(() => `custom-${Date.now()}`);
    const [currentAudio, setCurrentAudio] = useState<string | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const audioRef = useRef<HTMLAudioElement>(null);

    useEffect(() => {
        loadMessages();
    }, [sessionId]);

    useEffect(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    useEffect(() => {
        if (currentAudio && audioRef.current) {
            audioRef.current.src = currentAudio;
            audioRef.current.play().catch(console.error);
        }
    }, [currentAudio]);

    const loadMessages = async () => {
        try {
            const res = await api.get(`/custom_chat_bot/messages/${sessionId}`);
            setMessages(res.data.messages || []);
        } catch (e) {
            console.error("Failed to load messages:", e);
        }
    };

    const sendMessage = async () => {
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput("");
        setIsLoading(true);

        // Optimistic update
        const tempUserMsg: Message = {
            id: `temp-${Date.now()}`,
            session_id: sessionId,
            role: "user",
            content: userMessage,
            audio_url: null,
            created_at: new Date().toISOString()
        };
        setMessages(prev => [...prev, tempUserMsg]);

        try {
            const res = await api.post("/custom_chat_bot/chat", {
                session_id: sessionId,
                message: userMessage
            });

            // Add assistant response
            const assistantMsg: Message = res.data;
            setMessages(prev => [...prev.filter(m => !m.id.startsWith("temp-")), tempUserMsg, assistantMsg]);

            // Auto-play audio
            if (assistantMsg.audio_url) {
                const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001/api/v1';
                const serverBase = apiBase.replace('/api/v1', '');
                const fullUrl = `${serverBase}${assistantMsg.audio_url}`;
                setCurrentAudio(fullUrl);
            }
        } catch (e) {
            console.error("Failed to send message:", e);
            setMessages(prev => prev.filter(m => !m.id.startsWith("temp-")));
        } finally {
            setIsLoading(false);
        }
    };

    const clearSession = async () => {
        try {
            await api.delete(`/custom_chat_bot/messages/${sessionId}`);
            setMessages([]);
        } catch (e) {
            console.error("Failed to clear session:", e);
        }
    };

    const playAudio = (audioUrl: string | null) => {
        if (!audioUrl) return;
        const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9001/api/v1';
        const serverBase = apiBase.replace('/api/v1', '');
        const fullUrl = `${serverBase}${audioUrl}`;
        setCurrentAudio(fullUrl);
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4 md:p-8">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-2xl font-bold text-white mb-1">
                            🤖 Custom ChatBot - Test
                        </h1>
                        <p className="text-slate-400 text-sm">
                            Testez vos réponses configurées
                        </p>
                    </div>
                    <div className="flex gap-2">
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={clearSession}
                            className="bg-transparent border-white/20 text-white hover:bg-white/10"
                        >
                            <Trash2 className="w-4 h-4 mr-1" /> Effacer
                        </Button>
                        <Link href="/custom_chat_bot/conf">
                            <Button variant="outline" size="sm" className="bg-transparent border-white/20 text-white hover:bg-white/10">
                                <Settings className="w-4 h-4 mr-1" /> Config
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* Audio player (hidden) */}
                <audio ref={audioRef} className="hidden" />

                {/* Chat Container */}
                <Card className="bg-white/10 backdrop-blur border-white/20 h-[70vh] flex flex-col">
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-full text-slate-400">
                                <Bot className="w-16 h-16 mb-4 opacity-50" />
                                <p>Envoyez un message pour commencer !</p>
                                <p className="text-sm mt-2">
                                    Les réponses seront générées selon vos configurations.
                                </p>
                            </div>
                        )}

                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={cn(
                                    "flex gap-3",
                                    msg.role === "user" ? "flex-row-reverse" : ""
                                )}
                            >
                                <div className={cn(
                                    "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                                    msg.role === "user"
                                        ? "bg-purple-600"
                                        : "bg-gradient-to-br from-green-500 to-emerald-600"
                                )}>
                                    {msg.role === "user"
                                        ? <UserIcon className="w-4 h-4 text-white" />
                                        : <Bot className="w-4 h-4 text-white" />
                                    }
                                </div>
                                <div className={cn(
                                    "max-w-[75%] p-3 rounded-2xl",
                                    msg.role === "user"
                                        ? "bg-purple-600 text-white rounded-tr-sm"
                                        : "bg-white/20 text-white rounded-tl-sm"
                                )}>
                                    <p className="text-sm">{msg.content}</p>
                                    {msg.audio_url && msg.role === "assistant" && (
                                        <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() => playAudio(msg.audio_url)}
                                            className="mt-2 text-xs text-white/70 hover:text-white hover:bg-white/10 p-1 h-auto"
                                        >
                                            <Volume2 className="w-3 h-3 mr-1" /> Écouter
                                        </Button>
                                    )}
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                                    <Bot className="w-4 h-4 text-white" />
                                </div>
                                <div className="bg-white/20 p-3 rounded-2xl rounded-tl-sm">
                                    <Loader2 className="w-5 h-5 animate-spin text-white" />
                                </div>
                            </div>
                        )}

                        <div ref={scrollRef} />
                    </div>

                    {/* Input */}
                    <div className="p-4 border-t border-white/10">
                        <div className="flex gap-2">
                            <Input
                                placeholder="Écrivez votre message..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                                disabled={isLoading}
                                className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-slate-400"
                            />
                            <Button
                                onClick={sendMessage}
                                disabled={isLoading || !input.trim()}
                                className="bg-purple-600 hover:bg-purple-700"
                            >
                                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                            </Button>
                        </div>
                    </div>
                </Card>

                {/* Footer */}
                <div className="mt-4 text-center text-xs text-slate-500">
                    Custom ChatBot Test • Session: {sessionId.slice(-8)}
                </div>
            </div>
        </div>
    );
}
