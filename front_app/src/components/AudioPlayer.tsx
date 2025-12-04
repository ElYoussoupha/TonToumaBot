"use client";

import { useEffect, useRef, useState } from "react";
import { Play, Pause, Volume2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider"; // Assuming Slider is available or I'll use standard input

// Since I didn't install Slider specifically, I'll use a simple HTML audio element wrapped in a nice UI
// or just a hidden audio element controlled by buttons.

export function AudioPlayer({ src, autoPlay = false }: { src: string; autoPlay?: boolean }) {
    const audioRef = useRef<HTMLAudioElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);

    useEffect(() => {
        if (autoPlay && audioRef.current) {
            audioRef.current.play().catch(console.error);
        }
    }, [src, autoPlay]);

    const togglePlay = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    const onEnded = () => {
        setIsPlaying(false);
    };

    return (
        <div className="flex items-center space-x-2 rounded-full bg-slate-100 px-4 py-2">
            <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 rounded-full bg-white shadow-sm hover:bg-slate-50"
                onClick={togglePlay}
            >
                {isPlaying ? (
                    <Pause className="h-4 w-4 text-slate-700" />
                ) : (
                    <Play className="h-4 w-4 text-slate-700" />
                )}
            </Button>
            <div className="flex-1">
                {/* Visualizer could go here */}
                <div className="h-1 w-24 rounded-full bg-slate-300">
                    <div
                        className="h-full rounded-full bg-indigo-500 transition-all"
                        style={{ width: isPlaying ? "100%" : "0%" }} // Simple animation
                    />
                </div>
            </div>
            <audio
                ref={audioRef}
                src={src}
                onEnded={onEnded}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
                className="hidden"
            />
        </div>
    );
}
