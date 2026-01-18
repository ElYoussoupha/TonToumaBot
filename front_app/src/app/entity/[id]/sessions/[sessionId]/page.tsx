"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, User, Bot, Play, Pause } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import api from "@/lib/api";
import { Message } from "@/types";

// Define local AudioPlayer to avoid complex import dependencies if not available globally
const AudioPlayer = ({ src }: { src: string }) => {
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);

    const togglePlay = () => {
        if (!audioRef.current) return;
        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    return (
        <div className="flex items-center space-x-2 mt-2">
            <Button
                size="icon"
                variant="outline"
                className="h-8 w-8 rounded-full"
                onClick={togglePlay}
            >
                {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
            <span className="text-xs text-muted-foreground">Audio Message</span>
            <audio
                ref={audioRef}
                src={`${process.env.NEXT_PUBLIC_API_URL}/${src}`}
                onEnded={() => setIsPlaying(false)}
                className="hidden"
            />
        </div>
    );
};

export default function SessionDetailPage() {
    const params = useParams();
    const router = useRouter();
    const sessionId = params.sessionId as string;
    const entityId = params.id as string;
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMessages = async () => {
            try {
                // Use the session messages endpoint we inspected earlier
                // GET /api/v1/sessions/{session_id}/messages
                const res = await api.get<Message[]>(`/sessions/${sessionId}/messages`);
                setMessages(res.data);
            } catch (error) {
                console.error("Failed to fetch messages", error);
            } finally {
                setLoading(false);
            }
        };

        if (sessionId) {
            fetchMessages();
        }
    }, [sessionId]);

    if (loading) {
        return <div>Chargement des messages...</div>;
    }

    return (
        <div className="space-y-6 h-[calc(100vh-100px)] flex flex-col">
            <div className="flex items-center space-x-4">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <ArrowLeft className="h-5 w-5" />
                </Button>
                <div>
                    <h1 className="text-2xl font-bold tracking-tight">Détail de la Session</h1>
                    <p className="text-sm text-muted-foreground font-mono">{sessionId}</p>
                </div>
            </div>

            <ScrollArea className="flex-1 p-4 rounded-md border bg-slate-50">
                <div className="space-y-4 max-w-3xl mx-auto">
                    {messages.map((msg) => {
                        const isUser = msg.role === "user";
                        const isTool = msg.role === "tool";

                        if (isTool) {
                            return (
                                <div key={msg.message_id} className="flex justify-center my-4">
                                    <Badge variant="outline" className="text-xs font-mono text-muted-foreground">
                                        System (Tool): {msg.content?.substring(0, 50)}...
                                    </Badge>
                                </div>
                            )
                        }

                        return (
                            <div
                                key={msg.message_id}
                                className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
                            >
                                <div
                                    className={`flex max-w-[80%] ${isUser ? "flex-row-reverse" : "flex-row"
                                        } items-start gap-2`}
                                >
                                    <div
                                        className={`flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-full border ${isUser ? "bg-primary text-primary-foreground" : "bg-muted"
                                            }`}
                                    >
                                        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                    </div>
                                    <Card className={`p-3 ${isUser ? "bg-primary text-primary-foreground" : "bg-white"}`}>
                                        {/* 
                                            CRITICAL: Display 'content' which is the raw transcription for User 
                                            and the output text for Assistant.
                                            Do NOT use 'translated_content' for display unless debugging.
                                        */}
                                        <p className="text-sm whitespace-pre-wrap">{msg.content || "..."}</p>

                                        {msg.translated_content && (
                                            <div className={`mt-2 text-xs border-t pt-2 ${isUser ? "border-primary-foreground/20 text-primary-foreground/70" : "border-slate-100 text-muted-foreground"}`}>
                                                <span className="font-semibold text-[10px] uppercase">Traduction (Interne):</span>
                                                <p>{msg.translated_content}</p>
                                            </div>
                                        )}

                                        {msg.audio_path && <AudioPlayer src={msg.audio_path} />}
                                    </Card>
                                </div>
                            </div>
                        );
                    })}
                    {messages.length === 0 && (
                        <div className="text-center text-muted-foreground py-10">Aucun message dans cette session.</div>
                    )}
                </div>
            </ScrollArea>
        </div>
    );
}
