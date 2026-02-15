import React, { useState, useEffect } from "react";
import { LayoutDashboard, Target, History, Settings, Users, Search, Layers, Brain, TrendingUp, Shield } from "lucide-react";
import { cn } from "../../lib/utils";
import { Link, useLocation, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ConnectionStatus } from "../common/ConnectionStatus";

interface AppLayoutProps {
    children?: React.ReactNode;
}

const SidebarItem = ({ icon: Icon, label, path }: { icon: any, label: string, path: string }) => {
    const location = useLocation();
    const active = location.pathname === path;

    return (
        <Link to={path}>
            <div className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-xl cursor-pointer transition-all duration-200 group relative overflow-hidden border",
                active
                    ? "bg-linear-to-r from-primary/20 to-secondary/10 text-foreground border-primary/40 shadow-[0_6px_22px_rgba(25,217,160,0.2)]"
                    : "text-muted border-transparent hover:bg-white/5 hover:text-foreground hover:border-white/10"
            )}>
                {active && <div className="absolute inset-0 bg-linear-to-r from-primary/10 to-secondary/10 blur-xl" />}
                <Icon size={20} className={cn("transition-transform group-hover:scale-110 relative z-10", active && "scale-110")} />
                <span className="font-medium text-sm tracking-wide relative z-10">{label}</span>
                {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-secondary shadow-[0_0_10px_rgba(211,170,74,0.6)] relative z-10" />}
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
        <div className="flex h-full w-full bg-background overflow-hidden font-sans text-foreground selection:bg-primary/30">
            {/* Sidebar */}
            <div className="w-64 shrink-0 border-r border-secondary/20 bg-linear-to-b from-[#0e1737] to-[#0a1128] backdrop-blur-xl flex flex-col p-6 z-20 shadow-[inset_-1px_0_0_rgba(211,170,74,0.1)]">
                <div className="flex items-center gap-2 mb-10 px-2">
                    <div className="w-8 h-8 rounded-lg bg-linear-to-br from-secondary to-amber-300 flex items-center justify-center shadow-lg shadow-secondary/30">
                        <Target className="text-slate-900" size={18} />
                    </div>
                    <span className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-linear-to-r from-secondary via-amber-100 to-secondary">
                        Karchain
                    </span>
                </div>

                <nav className="flex flex-col gap-2 flex-1">
                    <SidebarItem icon={LayoutDashboard} label="Dashboard" path="/" />
                    <SidebarItem icon={Users} label="Players" path="/players" />
                    <SidebarItem icon={Shield} label="Teams" path="/teams" />
                    <SidebarItem icon={Search} label="Props Finder" path="/props-finder" />
                    <SidebarItem icon={Layers} label="AI Parlay" path="/mixed-parlay" />
                    <SidebarItem icon={Brain} label="Genius Picks" path="/genius-picks" />
                    <SidebarItem icon={TrendingUp} label="Self Improvement" path="/self-improvement" />
                    <SidebarItem icon={Target} label="Analysis" path="/analysis" />
                    <SidebarItem icon={History} label="History" path="/history" />
                    <SidebarItem icon={Settings} label="Settings" path="/settings" />
                </nav>

                <div className="mt-auto pt-6 border-t border-secondary/20">
                    <div className="flex items-center gap-3 px-2 mb-4">
                        <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center border border-primary/30">
                            <span className="text-xs font-bold text-primary">{initials}</span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm font-medium">{displayName}</span>
                            <span className="text-xs text-secondary">VIP Table</span>
                        </div>
                    </div>

                    <div className="px-2 py-2 bg-white/5 rounded-lg flex flex-col gap-2 text-[10px] text-muted border border-white/10">
                        <div className="flex items-center justify-between">
                            <span>Data Updated:</span>
                            <span className="text-primary font-mono">{timeAgo}</span>
                        </div>
                        <div className="flex items-center justify-between border-t border-white/5 pt-2">
                            <span>Sync Status:</span>
                            <ConnectionStatus />
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <main className="flex-1 h-full overflow-y-auto relative bg-[radial-gradient(ellipse_at_top,var(--tw-gradient-stops))] from-[#12214a] via-background to-background">
                <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center mask-[linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-12 pointer-events-none" />
                <div className="absolute top-[-8rem] right-[-8rem] w-[24rem] h-[24rem] rounded-full bg-secondary/15 blur-3xl pointer-events-none" />
                <div className="absolute top-[-5rem] left-[20%] w-[20rem] h-[20rem] rounded-full bg-primary/12 blur-3xl pointer-events-none" />
                <div className="p-8 max-w-7xl mx-auto relative z-10 min-h-full">
                    {children || <Outlet />}
                </div>
            </main>
        </div>
    );
};
