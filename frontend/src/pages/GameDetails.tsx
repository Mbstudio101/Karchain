import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, Game, fetchGameTracker, GameTracker } from "../api";
import { ArrowLeft, TrendingUp, Activity, Zap } from "lucide-react";
import { cn } from "../lib/utils";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { motion } from "framer-motion";

const fetchGameDetails = async (id: string) => {
    const { data } = await api.get<Game>(`/games/${id}`);
    return data;
};

export const GameDetails: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const { data: game, isLoading } = useQuery<Game>({
        queryKey: ["game", id],
        queryFn: () => fetchGameDetails(id!),
        enabled: !!id,
        refetchInterval: (_query: any) => {
            const game = _query.state.data as Game | undefined;
            return game?.status === "Live" ? 30000 : false;
        }
    });

    const { data: tracker, isLoading: isTrackerLoading } = useQuery<GameTracker>({
        queryKey: ["tracker", id],
        queryFn: () => fetchGameTracker(id!),
        enabled: !!id,
        refetchInterval: (_query: any) => {
            return game?.status === "Live" ? 15000 : false;
        }
    });

    if (isLoading) return <div className="flex justify-center p-10"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" /></div>;
    if (!game) return <div className="p-10 text-center">Game not found</div>;

    const homeStats = game.home_team.stats[0] || { ppg: 0, opp_ppg: 0, win_pct: 0 };
    const awayStats = game.away_team.stats[0] || { ppg: 0, opp_ppg: 0, win_pct: 0 };

    const chartData = [
        { name: "PPG", Home: homeStats.ppg, Away: awayStats.ppg },
        { name: "Opp PPG", Home: homeStats.opp_ppg, Away: awayStats.opp_ppg },
        { name: "Win %", Home: homeStats.win_pct * 100, Away: awayStats.win_pct * 100 },
    ];

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                    <ArrowLeft size={20} />
                </button>
                <h1 className="text-2xl font-bold text-white">Matchup Analysis</h1>
            </div>

            {/* Scoreboard / Matchup Header */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center bg-card border border-white/5 rounded-3xl p-8 relative overflow-hidden">
                <div className="text-center">
                    <h2 className="text-3xl font-black text-white mb-2">{game.away_team.name}</h2>
                    <div className="text-sm text-muted">Away</div>
                </div>

                <div className="text-center relative z-10">
                    <div className="text-sm font-bold text-primary uppercase tracking-widest mb-2">VS</div>
                    <div className="text-xs text-muted">
                        {new Date(game.game_date).toLocaleDateString()}
                        <br />
                        {new Date(game.game_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>

                <div className="text-center">
                    <h2 className="text-3xl font-black text-white mb-2">{game.home_team.name}</h2>
                    <div className="text-sm text-muted">Home</div>
                </div>

                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-primary/10 blur-3xl rounded-full -z-0" />
            </div>

            {/* Stats Comparison Chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-card border border-white/5 rounded-2xl p-6"
                >
                    <div className="flex items-center gap-2 mb-6">
                        <Activity size={18} className="text-primary" />
                        <h3 className="font-bold text-white">Head-to-Head Stats</h3>
                    </div>

                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                <XAxis dataKey="name" stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#666" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#171717', border: '1px solid #333', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                />
                                <Legend />
                                <Bar dataKey="Away" fill="#3b82f6" radius={[4, 4, 0, 0]} name={game.away_team.name} />
                                <Bar dataKey="Home" fill="#10b981" radius={[4, 4, 0, 0]} name={game.home_team.name} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </motion.div>

                {/* Betting Trends (Mock) */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-card border border-white/5 rounded-2xl p-6"
                >
                    <div className="flex items-center gap-2 mb-6">
                        <TrendingUp size={18} className="text-primary" />
                        <h3 className="font-bold text-white">Betting Trends</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="p-4 bg-white/5 rounded-xl border-l-2 border-emerald-500">
                            <div className="text-sm font-bold text-white mb-1">{game.home_team.name} at Home</div>
                            <div className="text-xs text-muted">7-3 ATS in last 10 games</div>
                        </div>
                        <div className="p-4 bg-white/5 rounded-xl border-l-2 border-blue-500">
                            <div className="text-sm font-bold text-white mb-1">{game.away_team.name} on Road</div>
                            <div className="text-xs text-muted">4-6 ATS in last 10 games</div>
                        </div>
                        <div className="p-4 bg-white/5 rounded-xl border-l-2 border-orange-500">
                            <div className="text-sm font-bold text-white mb-1">Over/Under</div>
                            <div className="text-xs text-muted">Over is 4-1 in last 5 meetings</div>
                        </div>
                    </div>
                </motion.div>
            </div>

            {/* Live Tracker Feed */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="bg-card border border-white/5 rounded-2xl p-6"
            >
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <Zap size={18} className="text-primary" />
                        <h3 className="font-bold text-white">Live Game Tracker</h3>
                    </div>
                    {game.status === "Live" && (
                        <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                            <span className="text-[10px] font-bold text-red-500 uppercase tracking-widest">Live Updates Active</span>
                        </div>
                    )}
                </div>

                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                    {isTrackerLoading && !tracker ? (
                        <div className="flex justify-center p-10"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" /></div>
                    ) : tracker?.plays?.length ? (
                        tracker.plays.map((play: any, idx: number) => (
                            <motion.div
                                key={play.id || idx}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: idx * 0.05 }}
                                className={cn(
                                    "p-4 rounded-xl border border-white/5 bg-white/5 flex gap-4 items-start relative overflow-hidden",
                                    idx === 0 && game.status === "Live" && "border-primary/20 bg-primary/5 shadow-lg shadow-primary/5"
                                )}
                            >
                                {idx === 0 && game.status === "Live" && (
                                    <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
                                )}
                                <div className="text-xs font-mono font-bold text-muted min-w-[50px] pt-0.5">
                                    {play.clock}
                                </div>
                                <div className="flex flex-col gap-1 flex-1">
                                    <p className="text-sm text-white/90 leading-relaxed">{play.text}</p>
                                    {play.type && (
                                        <span className="text-[10px] font-bold text-muted uppercase tracking-wider">{play.type}</span>
                                    )}
                                </div>
                                {play.scoreValue && (
                                    <div className="text-xs font-black text-primary bg-primary/10 px-2 py-1 rounded">
                                        +{play.scoreValue}
                                    </div>
                                )}
                            </motion.div>
                        ))
                    ) : (
                        <div className="p-8 text-center text-muted italic border border-dashed border-white/10 rounded-xl bg-white/5">
                            {tracker?.message || "No play-by-play data available for this game yet."}
                        </div>
                    )}
                </div>
            </motion.div>
        </div>
    );
};
