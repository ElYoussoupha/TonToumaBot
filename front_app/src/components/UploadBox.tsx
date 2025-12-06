"use client";

import { useState, useRef } from "react";
import { Upload, File, X, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface UploadBoxProps {
    onUpload: (files: FileList) => Promise<void>;
    accept?: string;
    maxFiles?: number;
}

export function UploadBox({ onUpload, accept = "*", maxFiles = 1 }: UploadBoxProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            await processUpload(e.dataTransfer.files);
        }
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            await processUpload(e.target.files);
        }
    };

    const processUpload = async (files: FileList) => {
        setIsUploading(true);
        try {
            await onUpload(files);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    };

    return (
        <div
            className={cn(
                "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
                isDragging
                    ? "border-indigo-500 bg-indigo-50"
                    : "border-slate-300 hover:bg-slate-50",
                isUploading && "opacity-50 pointer-events-none"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept={accept}
                multiple={maxFiles > 1}
                onChange={handleFileSelect}
            />

            {isUploading ? (
                <Loader2 className="h-10 w-10 animate-spin text-indigo-500" />
            ) : (
                <Upload className="h-10 w-10 text-slate-400" />
            )}

            <div className="mt-4 text-center">
                <p className="text-sm font-medium text-slate-900">
                    {isUploading ? "Envoi en cours..." : "Glissez vos fichiers ici"}
                </p>
                <p className="mt-1 text-xs text-slate-500">ou</p>
                <Button
                    type="button"
                    variant="outline"
                    className="mt-2"
                    onClick={(e) => {
                        e.stopPropagation(); // Prevent bubbling if nested
                        fileInputRef.current?.click();
                    }}
                    disabled={isUploading}
                >
                    Parcourir les fichiers
                </Button>
            </div>
        </div>
    );
}
