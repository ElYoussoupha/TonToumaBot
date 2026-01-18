"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { Calendar, Clock, LogOut, User, LayoutGrid } from "lucide-react";
import { cn } from "@/lib/utils";

export default function DoctorLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();
    const pathname = usePathname();
    const [doctorName, setDoctorName] = useState("");
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        // Skip auth check on login page
        if (pathname === "/doctor/login") {
            setIsLoading(false);
            return;
        }

        // Check if logged in
        const token = localStorage.getItem("doctor_token");
        const name = localStorage.getItem("doctor_name");

        if (!token) {
            router.push("/doctor/login");
            return;
        }

        setDoctorName(name || "Médecin");
        setIsLoading(false);
    }, [pathname, router]);

    const handleLogout = () => {
        localStorage.removeItem("doctor_token");
        localStorage.removeItem("doctor_id");
        localStorage.removeItem("doctor_name");
        localStorage.removeItem("doctor_entity_id");
        router.push("/doctor/login");
    };

    // Login page doesn't use the layout
    if (pathname === "/doctor/login") {
        return <>{children}</>;
    }

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-muted-foreground">Chargement...</div>
            </div>
        );
    }

    const navigation = [
        { name: "Dashboard", href: "/doctor", icon: LayoutGrid },
        { name: "Mes créneaux", href: "/doctor/creneaux", icon: Clock },
        { name: "Mon calendrier", href: "/doctor/calendrier", icon: Calendar },
    ];

    return (
        <div className="flex h-screen overflow-hidden bg-gray-50">
            {/* Sidebar */}
            <div className="flex h-full w-64 flex-col bg-emerald-800 text-white">
                <div className="flex h-16 items-center justify-center border-b border-emerald-700 px-4">
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-emerald-600 flex items-center justify-center">
                            <User className="h-4 w-4" />
                        </div>
                        <span className="font-medium truncate">{doctorName}</span>
                    </div>
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
                                        ? "bg-emerald-700 text-white"
                                        : "text-emerald-200 hover:bg-emerald-700 hover:text-white"
                                )}
                            >
                                <item.icon
                                    className={cn(
                                        "mr-3 h-5 w-5 flex-shrink-0",
                                        isActive ? "text-white" : "text-emerald-300 group-hover:text-white"
                                    )}
                                    aria-hidden="true"
                                />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>
                <div className="border-t border-emerald-700 p-4">
                    <button
                        onClick={handleLogout}
                        className="flex w-full items-center rounded-md px-2 py-2 text-sm font-medium text-emerald-200 hover:bg-emerald-700 hover:text-white"
                    >
                        <LogOut className="mr-3 h-5 w-5 text-emerald-300" />
                        Déconnexion
                    </button>
                </div>
            </div>
            {/* Main content */}
            <main className="flex-1 overflow-y-auto p-8">
                {children}
            </main>
        </div>
    );
}
