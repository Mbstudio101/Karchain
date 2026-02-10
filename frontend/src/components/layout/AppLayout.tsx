import React, { useState, useEffect } from "react";
import { LayoutDashboard, Target, History, Settings, Users, Search, Layers, Brain, TrendingUp } from "lucide-react";
import { cn } from "../../lib/utils";
import { Link, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

interface AppLayoutProps {
    children?: React.ReactNode;
}

const SidebarItem = ({ icon: Icon, label, path }: { icon: any, label: string, path: string }) => {
    const location = useLocation();
    const active = location.pathname === path;

    return (
        <Link to={path}>
            <div className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 group relative overflow-hidden",
                active ? "bg-primary/10 text-primary" : "text-muted hover:bg-white/5 hover:text-foreground"
            )}>
                {active && <div className="absolute inset-0 bg-primary/5 blur-xl" />}
                <Icon size={20} className={cn("transition-transform group-hover:scale-110 relative z-10", active && "scale-110")} />
                <span className="font-medium text-sm tracking-wide relative z-10">{label}</span>
                {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_rgba(16,185,129,0.5)] relative z-10" />}
            </div>
        </Link>
    );
};

const formatTimeAgo = (date: Date): string => {
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 10) return "Just now";
    if (seconds < 60) return `${seconds}s ago`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    return `${Math.floor(minutes / 60)}h ago`;
};

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
    const { user } = useAuth();
    const [lastUpdated, setLastUpdated] = useState(new Date());
    const [timeAgo, setTimeAgo] = useState("Just now");

    // Track the most recent data fetch
    useEffect(() => {
        const interval = setInterval(() => {
            setTimeAgo(formatTimeAgo(lastUpdated));
        }, 5000);
        return () => clearInterval(interval);
    }, [lastUpdated]);

    // Listen for React Query refetch events (games refresh every 30s)
    useEffect(() => {
        const interval = setInterval(() => {
            setLastUpdated(new Date());
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const displayName = user?.full_name || user?.email?.split('@')[0] || "User";
    const initials = displayName.slice(0, 2).toUpperCase();

    return (
        <div className="flex h-screen w-full bg-background overflow-hidden font-sans text-foreground selection:bg-primary/30">
            {/* Sidebar */}
            <div className="w-64 shrink-0 border-r border-white/5 bg-card/50 backdrop-blur-xl flex flex-col p-6 z-20">
                <div className="flex items-center gap-2 mb-10 px-2">
                    <div className="w-8 h-8 rounded-lg bg-linear-to-br from-primary to-emerald-600 flex items-center justify-center shadow-lg shadow-primary/20">
                        <Target className="text-black" size={18} />
                    </div>
                    <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-linear-to-r from-white to-white/60">
                        Karchain
                    </span>
                </div>

                <nav className="flex flex-col gap-2 flex-1">
                    <SidebarItem icon={LayoutDashboard} label="Dashboard" path="/" />
                    <SidebarItem icon={Users} label="Players" path="/players" />
                    <SidebarItem icon={Search} label="Props Finder" path="/props-finder" />
                    <SidebarItem icon={Layers} label="AI Parlay" path="/mixed-parlay" />
                    <SidebarItem icon={Brain} label="Genius Picks" path="/genius-picks" />
                    <SidebarItem icon={TrendingUp} label="Self Improvement" path="/self-improvement" />
                    <SidebarItem icon={Target} label="Analysis" path="/analysis" />
                    <SidebarItem icon={History} label="History" path="/history" />
                    <SidebarItem icon={Settings} label="Settings" path="/settings" />
                </nav>

                <div className="mt-auto pt-6 border-t border-white/5">
                    <div className="flex items-center gap-3 px-2 mb-4">
                        <div className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center border border-secondary/30">
                            <span className="text-xs font-bold text-secondary">{initials}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium">{displayName}</span>
                            <span className="text-xs text-muted">Pro Plan</span>
                        </div>
                    </div>

                    <div className="px-2 py-2 bg-white/5 rounded-lg flex items-center justify-between text-[10px] text-muted">
                        <span>Data Updated:</span>
                        <span className="text-emerald-400 font-mono">{timeAgo}</span>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="flex-1 h-full overflow-y-auto relative bg-[radial-gradient(ellipse_at_top,var(--tw-gradient-stops))] from-slate-900 via-background to-background">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center mask-[linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-20 pointer-events-none" />
                <div className="p-8 max-w-7xl mx-auto relative z-10 min-h-full">
                    {children || <Outlet />}
                </div>
            </main>
        </div>
    );
};
