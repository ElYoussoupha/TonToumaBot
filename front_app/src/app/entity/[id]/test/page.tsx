"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
// import { ScrollArea } from "@/components/ui/scroll-area"; // Removed as it might be missing
import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioPlayer } from "@/components/AudioPlayer";
import api from "@/lib/api";
import { Message, Instance } from "@/types";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function TestChatbotPage() {
    const params = useParams();
    const entityId = params.id as string;
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentAudioResponse, setCurrentAudioResponse] = useState<string | null>(null);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [textInput, setTextInput] = useState<string>("");

    // Fetch valid instance ID
    const [instanceId, setInstanceId] = useState<string>("");

    useEffect(() => {
        const fetchInstances = async () => {
            try {
                const res = await api.get<Instance[]>("/instances");
                const entityInstances = (res.data || []).filter((i: Instance) => i.entity_id === entityId);
                if (entityInstances.length > 0) {
                    setInstanceId(entityInstances[0].instance_id);
                } else {
                    console.warn("No instances found for this entity");
                }
            } catch (error) {
                console.error("Failed to fetch instances", error);
            }
        };

        if (entityId) {
            fetchInstances();
        }
    }, [entityId]);

    const buildUploadsUrl = (path?: string | null) => {
        if (!path) return null;
        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '') || 'http://localhost:9000';
        // If path already absolute (http), return as is
        if (path.startsWith('http://') || path.startsWith('https://')) return path;
        return `${baseUrl}/${path.replace(/^\//, '')}`;
    };

    const handleSendText = async () => {
        const text = textInput.trim();
        if (!text || !instanceId) return;
        setIsProcessing(true);

        // optimistic user message
        const tempUserMsg: Message = {
            message_id: `${Date.now()}-text`,
            session_id: sessionId || "temp",
            instance_id: instanceId,
            role: "user",
            content: text,
            created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, tempUserMsg]);
        setTextInput("");

        try {
            const res = await api.post("/chat/text", { instance_id: instanceId, text });
            const data = res.data;

            if (data.session_id) setSessionId(data.session_id);

            const assistantMsg: Message = {
                message_id: `${Date.now()}-assistant`,
                session_id: data.session_id,
                instance_id: instanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, assistantMsg]);

            if (data.response_audio) {
                const audioUrl = buildUploadsUrl(data.response_audio);
                if (audioUrl) setCurrentAudioResponse(audioUrl);
            }
        } catch (error) {
            console.error("Text chat error", error);
            setMessages((prev) => ([
                ...prev,
                {
                    message_id: `${Date.now()}-error`,
                    session_id: "error",
                    instance_id: instanceId,
                    role: "system",
                    content: "Erreur lors de l'envoi du message texte.",
                    created_at: new Date().toISOString(),
                },
            ]));
        } finally {
            setIsProcessing(false);
        }
    };

    useEffect(() => {
        const fetchHistory = async () => {
            if (!sessionId) return;
            try {
                const res = await api.get<Message[]>(`/sessions/${sessionId}/messages`);
                const msgs: Message[] = (res.data || []).map((m: Message) => ({
                    ...m,
                    audio_path: buildUploadsUrl(m.audio_path) || undefined,
                }));
                setMessages(msgs);
            } catch (e) {
                console.error('Failed to fetch session messages', e);
            }
        };
        fetchHistory();
    }, [sessionId]);

    const handleAudioRecord = async (audioBlob: Blob) => {
        setIsProcessing(true);
        setCurrentAudioResponse(null);

        // 1. Create optimistic user message
        const tempUserMsg: Message = {
            message_id: Date.now().toString(),
            session_id: sessionId || "temp",
            instance_id: instanceId,
            role: "user",
            content: "🎤 Audio envoyé...",
            created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, tempUserMsg]);

        const formData = new FormData();
        formData.append("audio_file", audioBlob, "recording.wav");
        formData.append("instance_id", instanceId); // We need a valid UUID here usually
        // formData.append("speaker_id", ...); 

        try {
            // We need a valid UUID for instance_id, let's fetch one if "test-instance" is invalid
            // Or just let the backend handle the error if it expects UUID

            const res = await api.post("/chat/messages", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            const data = res.data;

            // Persist session id
            if (data.session_id) {
                setSessionId(data.session_id);
            }

            // Update user message with transcription if available (assuming backend returns it)
            // For now, we'll just add the assistant response

            const assistantMsg: Message = {
                message_id: Date.now().toString(),
                session_id: data.session_id,
                instance_id: instanceId,
                role: "assistant",
                content: data.response_text,
                audio_path: buildUploadsUrl(data.response_audio) || undefined,
                created_at: new Date().toISOString(),
            };

            setMessages((prev) => {
                const newMsgs = [...prev];
                // Update last user message with transcription and audio url if available
                const lastIdx = newMsgs.length - 1;
                if (lastIdx >= 0 && newMsgs[lastIdx].role === 'user') {
                    newMsgs[lastIdx] = {
                        ...newMsgs[lastIdx],
                        content: data.transcription || newMsgs[lastIdx].content,
                        audio_path: buildUploadsUrl(data.user_audio) || newMsgs[lastIdx].audio_path,
                        session_id: data.session_id || newMsgs[lastIdx].session_id,
                    } as Message;
                }
                return [...newMsgs, assistantMsg];
            });

            if (data.response_audio) {
                const audioUrl = buildUploadsUrl(data.response_audio);
                if (audioUrl) setCurrentAudioResponse(audioUrl);
            }

        } catch (error) {
            console.error("Chat error", error);
            setMessages((prev) => [
                ...prev,
                {
                    message_id: Date.now().toString(),
                    session_id: "error",
                    instance_id: instanceId,
                    role: "system",
                    content: "Erreur lors du traitement de la demande.",
                    created_at: new Date().toISOString(),
                },
            ]);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <h1 className="text-3xl font-bold tracking-tight">Test du Chatbot</h1>

            <Card className="flex-1 overflow-hidden bg-slate-50">
                <CardContent className="flex h-full flex-col p-4">
                    <div className="flex-1 overflow-y-auto space-y-4 pr-4">
                        {messages.length === 0 && (
                            <div className="flex h-full items-center justify-center text-muted-foreground">
                                Aucun message. Commencez à parler !
                            </div>
                        )}
                        {messages.map((msg) => (
                            <div
                                key={msg.message_id}
                                className={cn(
                                    "flex w-full",
                                    msg.role === "user" ? "justify-end" : "justify-start"
                                )}
                            >
                                <div
                                    className={cn(
                                        "max-w-[80%] rounded-lg px-4 py-2 shadow-sm",
                                        msg.role === "user"
                                            ? "bg-indigo-600 text-white"
                                            : msg.role === "system"
                                                ? "bg-red-100 text-red-800"
                                                : "bg-white text-slate-800"
                                    )}
                                >
                                    <p className="text-sm">{msg.content}</p>
                                    {msg.audio_path && (
                                        <div className="mt-2">
                                            <AudioPlayer src={msg.audio_path} />
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>

                    {currentAudioResponse && (
                        <div className="mt-4 flex justify-center">
                            <AudioPlayer src={currentAudioResponse} autoPlay />
                        </div>
                    )}
                </CardContent>
            </Card>

            <div className="flex flex-col gap-4 justify-center py-4">
                {instanceId ? (
                    <AudioRecorder onRecordingComplete={handleAudioRecord} isProcessing={isProcessing} />
                ) : (
                    <div className="text-red-500">Aucune instance disponible pour ce chatbot. Veuillez en créer une.</div>
                )}
                <div className="flex items-center gap-2">
                    <Input
                        placeholder="Tapez un message..."
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter') handleSendText(); }}
                    />
                    <Button onClick={handleSendText} disabled={!textInput.trim() || !instanceId || isProcessing}>
                        Envoyer
                    </Button>
                </div>
            </div>
        </div>
    );
}
