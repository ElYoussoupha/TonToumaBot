"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { Home, Database, Server, MessageSquare, PlayCircle, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";

export function EntitySidebar() {
    const pathname = usePathname();
    const params = useParams();
    const entityId = params.id as string;
    const { currentEntity } = useAppStore();

    const navigation = [
        { name: "Accueil", href: `/entity/${entityId}`, icon: Home },
        { name: "Base de connaissance", href: `/entity/${entityId}/knowledge`, icon: Database },
        { name: "Instances", href: `/entity/${entityId}/instances`, icon: Server },
        { name: "Sessions", href: `/entity/${entityId}/sessions`, icon: MessageSquare },
        { name: "Test Chatbot", href: `/entity/${entityId}/test`, icon: PlayCircle },
    ];

    return (
        <div className="flex h-full w-64 flex-col bg-indigo-900 text-white">
            <div className="flex h-16 items-center justify-center border-b border-indigo-800 px-4">
                <h1 className="text-lg font-bold truncate">
                    {currentEntity?.name || "Espace Entité"}
                </h1>
            </div>
            <nav className="flex-1 space-y-1 px-2 py-4">
                {navigation.map((item) => {
                    const isActive = pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            href={item.href}
                            className={cn(
                                "group flex items-center rounded-md px-2 py-2 text-sm font-medium transition-colors",
                                isActive
                                    ? "bg-indigo-800 text-white"
                                    : "text-indigo-200 hover:bg-indigo-800 hover:text-white"
                            )}
                        >
                            <item.icon
                                className={cn(
                                    "mr-3 h-5 w-5 flex-shrink-0",
                                    isActive ? "text-white" : "text-indigo-300 group-hover:text-white"
                                )}
                                aria-hidden="true"
                            />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>
            <div className="border-t border-indigo-800 p-4">
                <Link
                    href="/admin/entities"
                    className="flex w-full items-center rounded-md px-2 py-2 text-sm font-medium text-indigo-200 hover:bg-indigo-800 hover:text-white"
                >
                    <ArrowLeft className="mr-3 h-5 w-5 text-indigo-300" />
                    Retour Admin
                </Link>
            </div>
        </div>
    );
}
