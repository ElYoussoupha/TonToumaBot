"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area"; // Need to check if ScrollArea is installed, if not use div
import { AudioRecorder } from "@/components/AudioRecorder";
import { AudioPlayer } from "@/components/AudioPlayer";
import api from "@/lib/api";
import { Message } from "@/types";
import { cn } from "@/lib/utils";

export default function TestChatbotPage() {
    const params = useParams();
    const entityId = params.id as string;
    const [messages, setMessages] = useState<Message[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentAudioResponse, setCurrentAudioResponse] = useState<string | null>(null);

    // Mock instance ID for testing - in real app, select from available instances
    // For now we'll just use a placeholder or fetch one
    const [instanceId, setInstanceId] = useState("test-instance");

    const handleAudioRecord = async (audioBlob: Blob) => {
        setIsProcessing(true);
        setCurrentAudioResponse(null);

        // 1. Create optimistic user message
        const tempUserMsg: Message = {
            message_id: Date.now().toString(),
            session_id: "temp",
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

            const res = await api.post("/messages", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });

            const data = res.data;

            // Update user message with transcription if available (assuming backend returns it)
            // For now, we'll just add the assistant response

            const assistantMsg: Message = {
                message_id: Date.now().toString(),
                session_id: data.session_id,
                instance_id: instanceId,
                role: "assistant",
                content: data.response_text,
                created_at: new Date().toISOString(),
            };

            setMessages((prev) => {
                const newMsgs = [...prev];
                // Update the last user message content if we had transcription
                // newMsgs[newMsgs.length - 1].content = data.transcription; 
                return [...newMsgs, assistantMsg];
            });

            if (data.response_audio) {
                // Assuming backend returns a path or URL. 
                // If it's a local path, we might need to proxy it or use a proper URL
                // For this demo, let's assume the backend serves it statically or we get a URL
                // If it returns a file path like "uploads/...", we need to prepend API URL
                const audioUrl = `${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')}/${data.response_audio}`;
                setCurrentAudioResponse(audioUrl);
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

            <div className="flex justify-center py-4">
                <AudioRecorder onRecordingComplete={handleAudioRecord} isProcessing={isProcessing} />
            </div>
        </div>
    );
}
