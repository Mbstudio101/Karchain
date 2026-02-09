import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Brain, Flame, Snowflake, RefreshCw, Award } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface GeniusPick {
    player: string;
    prop: string;
    line: number;
    pick: string;
    odds: number;
    ev: string;
    edge: string;
    kelly_bet: string;
    hit_rate: string;
    streak: string;
    confidence_range: string;
    grade: string;
}

interface GeniusPicksResponse {
    genius_count: number;
    picks: GeniusPick[];
}

const fetchGeniusPicks = async (): Promise<GeniusPicksResponse> => {
    const { data } = await api.get<GeniusPicksResponse>("/recommendations/genius-picks");
    return data;
};

export const GeniusPicksPage: React.FC = () => {
    const { data, isLoading, refetch, isFetching } = useQuery({
        queryKey: ["geniusPicks"],
        queryFn: fetchGeniusPicks,
        staleTime: 1000 * 60 * 5
    });

    const getStreakIcon = (streak: string) => {
        if (streak === "hot") return <Flame size={14} className="text-orange-400" />;
        if (streak === "cold") return <Snowflake size={14} className="text-blue-400" />;
        return null;
    };

    const getGradeColor = (grade: string) => {
        if (grade === "A+") return "from-yellow-400 to-orange-500";
        return "from-emerald-400 to-emerald-600";
    };

    const aPlusCount = data?.picks.filter(p => p.grade === "A+").length || 0;
    const aCount = data?.picks.filter(p => p.grade === "A").length || 0;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl">
                        <Brain className="text-purple-400" size={28} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Genius Picks</h1>
                        <p className="text-sm text-muted">A/A+ Grade • Kelly Optimized • Positive EV Only</p>
                    </div>
                </div>
                <button
                    onClick={() => refetch()}
                    disabled={isFetching}
                    className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-white/10 px-4 py-2 rounded-xl transition-colors"
                >
                    <RefreshCw size={16} className={isFetching ? "animate-spin" : ""} />
                    <span className="text-sm">Refresh</span>
                </button>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-card border border-white/10 rounded-xl p-4">
                    <div className="text-xs text-muted uppercase tracking-wider mb-1">Total Picks</div>
                    <div className="text-3xl font-bold text-white">{data?.genius_count || 0}</div>
                </div>
                <div className="bg-gradient-to-br from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 rounded-xl p-4">
                    <div className="text-xs text-yellow-400 uppercase tracking-wider mb-1">A+ Grade</div>
                    <div className="text-3xl font-bold text-yellow-400">{aPlusCount}</div>
                </div>
                <div className="bg-gradient-to-br from-emerald-500/10 to-green-500/10 border border-emerald-500/20 rounded-xl p-4">
                    <div className="text-xs text-emerald-400 uppercase tracking-wider mb-1">A Grade</div>
                    <div className="text-3xl font-bold text-emerald-400">{aCount}</div>
                </div>
                <div className="bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/20 rounded-xl p-4">
                    <div className="text-xs text-purple-400 uppercase tracking-wider mb-1">Avg Edge</div>
                    <div className="text-3xl font-bold text-purple-400">
                        {data?.picks.length
                            ? `+${(data.picks.reduce((sum, p) => sum + parseFloat(p.edge.replace('+', '').replace('%', '')), 0) / data.picks.length).toFixed(1)}%`
                            : "0%"
                        }
                    </div>
                </div>
            </div>

            {/* Picks Grid */}
            {isLoading ? (
                <div className="flex justify-center p-12">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-400" />
                </div>
            ) : !data?.picks?.length ? (
                <div className="text-center py-16 text-muted">
                    <Brain size={48} className="mx-auto mb-4 opacity-20" />
                    <p>No genius picks available right now</p>
                    <p className="text-xs opacity-50 mt-1">Requires 10+ game sample with 5%+ edge</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <AnimatePresence>
                        {data.picks.map((pick, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.03 }}
                                className="bg-card border border-white/10 rounded-xl p-5 hover:border-purple-500/30 transition-all hover:shadow-xl hover:shadow-purple-500/5"
                            >
                                {/* Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex items-center gap-2">
                                        <div className={`text-xs font-black px-2.5 py-1 rounded-full bg-gradient-to-r ${getGradeColor(pick.grade)} text-black`}>
                                            {pick.grade}
                                        </div>
                                        {getStreakIcon(pick.streak)}
                                    </div>
                                    <div className="text-right">
                                        <div className="text-lg font-bold text-emerald-400">{pick.ev}</div>
                                        <div className="text-[10px] text-muted">per $100</div>
                                    </div>
                                </div>

                                {/* Player & Prop */}
                                <div className="mb-4">
                                    <div className="font-bold text-white text-lg mb-1">{pick.player}</div>
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="text-muted">{pick.prop}</span>
                                        <span className="text-white font-bold">{pick.line}</span>
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${pick.pick === "OVER" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                                            {pick.pick}
                                        </span>
                                    </div>
                                </div>

                                {/* Stats Grid */}
                                <div className="grid grid-cols-2 gap-3 text-xs">
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <div className="text-muted mb-0.5">Odds</div>
                                        <div className="font-bold text-white">{pick.odds > 0 ? `+${pick.odds}` : pick.odds}</div>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <div className="text-muted mb-0.5">Edge</div>
                                        <div className="font-bold text-emerald-400">{pick.edge}</div>
                                    </div>
                                    <div className="bg-white/5 rounded-lg p-2">
                                        <div className="text-muted mb-0.5">Hit Rate</div>
                                        <div className="font-bold text-white">{pick.hit_rate}</div>
                                    </div>
                                    <div className="bg-purple-500/10 rounded-lg p-2">
                                        <div className="text-muted mb-0.5">Kelly Bet</div>
                                        <div className="font-bold text-purple-400">{pick.kelly_bet}</div>
                                    </div>
                                </div>

                                {/* Confidence Range */}
                                <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
                                    <span className="text-muted">Confidence Range</span>
                                    <span className="text-white/70">{pick.confidence_range}</span>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Legend */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-4 mt-6">
                <h4 className="text-sm font-bold text-white mb-3 flex items-center gap-2">
                    <Award size={14} className="text-yellow-400" />
                    Understanding Genius Picks
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-muted">
                    <div>
                        <span className="text-yellow-400 font-bold">A+ Grade</span>: EV &gt; $5 per $100 bet
                    </div>
                    <div>
                        <span className="text-emerald-400 font-bold">A Grade</span>: EV &gt; $3 per $100 bet
                    </div>
                    <div>
                        <span className="text-purple-400 font-bold">Kelly Bet</span>: Optimal size for $1000 bankroll
                    </div>
                    <div>
                        <Flame size={12} className="inline text-orange-400" /> = Hot streak (recent performance above average)
                    </div>
                    <div>
                        <Snowflake size={12} className="inline text-blue-400" /> = Cold streak (recent performance below average)
                    </div>
                    <div>
                        <span className="text-white">Edge</span>: Your advantage vs. implied odds
                    </div>
                </div>
            </div>
        </div>
    );
};
