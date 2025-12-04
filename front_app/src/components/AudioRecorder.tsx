"use client";

import { useState, useRef } from "react";
import { Mic, Square, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface AudioRecorderProps {
    onRecordingComplete: (blob: Blob) => void;
    isProcessing?: boolean;
}

export function AudioRecorder({ onRecordingComplete, isProcessing = false }: AudioRecorderProps) {
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorderRef.current = new MediaRecorder(stream);
            chunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorderRef.current.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: "audio/wav" });
                onRecordingComplete(blob);
                stream.getTracks().forEach((track) => track.stop());
            };

            mediaRecorderRef.current.start();
            setIsRecording(true);
        } catch (error) {
            console.error("Error accessing microphone:", error);
            alert("Impossible d'accéder au microphone");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center space-y-4">
            <div
                className={cn(
                    "relative flex h-24 w-24 items-center justify-center rounded-full transition-all duration-300",
                    isRecording ? "bg-red-100 animate-pulse" : "bg-slate-100",
                    isProcessing && "bg-indigo-100"
                )}
            >
                {isProcessing ? (
                    <Loader2 className="h-10 w-10 animate-spin text-indigo-600" />
                ) : isRecording ? (
                    <Square
                        className="h-10 w-10 cursor-pointer text-red-600"
                        onClick={stopRecording}
                    />
                ) : (
                    <Mic
                        className="h-10 w-10 cursor-pointer text-slate-600 hover:text-indigo-600"
                        onClick={startRecording}
                    />
                )}
            </div>
            <p className="text-sm font-medium text-slate-600">
                {isProcessing
                    ? "Traitement en cours..."
                    : isRecording
                        ? "Enregistrement... (Cliquer pour arrêter)"
                        : "Cliquer pour parler"}
            </p>
        </div>
    );
}
