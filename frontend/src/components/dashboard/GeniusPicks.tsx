import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchGeniusPicks } from "../../api";
import { Brain, Flame, Snowflake } from "lucide-react";
import { motion } from "framer-motion";

export const GeniusPicks: React.FC = () => {
    const { data, isLoading, refetch } = useQuery({
        queryKey: ["geniusPicks"],
        queryFn: fetchGeniusPicks,
        staleTime: 1000 * 60 * 5
    });

    const getStreakIcon = (streak: string) => {
        if (streak === "hot") return <Flame size={12} className="text-orange-400" />;
        if (streak === "cold") return <Snowflake size={12} className="text-blue-400" />;
        return null;
    };

    const getGradeColor = (grade: string) => {
        if (grade === "S") return "from-amber-300 to-red-500";
        if (grade === "A+") return "from-yellow-400 to-orange-500";
        if (grade === "A") return "from-emerald-400 to-emerald-600";
        if (grade === "B+") return "from-blue-400 to-blue-600";
        return "from-gray-400 to-gray-600";
    };

    if (isLoading) {
        return (
            <div className="bg-card border border-white/10 rounded-2xl p-6">
                <div className="flex items-center gap-2 mb-4">
                    <Brain className="text-purple-400" size={20} />
                    <h3 className="font-bold text-white">Genius Picks</h3>
                </div>
                <div className="flex justify-center p-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-400" />
                </div>
            </div>
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-br from-purple-900/20 to-indigo-900/20 border border-purple-500/20 rounded-2xl p-6"
        >
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="p-2 bg-purple-500/20 rounded-lg">
                        <Brain className="text-purple-400" size={20} />
                    </div>
                    <div>
                        <h3 className="font-bold text-white">Genius Picks</h3>
                        <p className="text-[10px] text-purple-300/70">A+ Grade • Kelly Optimized • High EV</p>
                    </div>
                </div>
                <button
                    onClick={() => refetch()}
                    className="text-xs text-purple-400 hover:text-purple-300 transition-colors"
                >
                    Refresh
                </button>
            </div>

            {!data?.picks?.length ? (
                <div className="text-center py-8 text-muted text-sm">
                    No genius picks available right now.<br />
                    <span className="text-xs opacity-50">Requires 10+ game sample with 5%+ edge</span>
                </div>
            ) : (
                <div className="space-y-3">
                    {data.picks.slice(0, 5).map((pick, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="bg-white/5 rounded-xl p-3 border border-purple-500/20 hover:border-purple-500/40 transition-colors"
                        >
                            <div className="flex items-start justify-between mb-2">
                                <div className="flex items-center gap-2">
                                    <div className={`text-[10px] font-black px-2 py-0.5 rounded-full bg-gradient-to-r ${getGradeColor(pick.grade)} text-black`}>
                                        {pick.grade}
                                    </div>
                                    <span className="font-bold text-white text-sm">{pick.player}</span>
                                    {getStreakIcon(pick.streak)}
                                </div>
                                <div className="text-right">
                                    <div className="text-emerald-400 font-bold text-sm">{pick.ev}</div>
                                    <div className="text-[9px] text-muted">per $100</div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 mb-2">
                                <span className="text-xs text-muted">{pick.prop}</span>
                                <span className="text-white font-bold">{pick.line}</span>
                                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${pick.pick === "OVER" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                                    {pick.pick}
                                </span>
                                <span className="text-xs text-muted">{pick.odds > 0 ? `+${pick.odds}` : pick.odds}</span>
                            </div>

                            <div className="grid grid-cols-4 gap-2 text-[10px]">
                                <div className="text-center">
                                    <div className="text-muted">Edge</div>
                                    <div className="text-emerald-400 font-bold">{pick.edge}</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-muted">Hit Rate</div>
                                    <div className="text-white font-bold">{pick.hit_rate}</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-muted">Kelly Bet</div>
                                    <div className="text-purple-400 font-bold">{pick.kelly_bet}</div>
                                </div>
                                <div className="text-center">
                                    <div className="text-muted">Range</div>
                                    <div className="text-white/70">{pick.confidence_range}</div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>
            )}

            {data && data.genius_count > 5 && (
                <div className="mt-4 text-center">
                    <span className="text-xs text-purple-400">{data.genius_count - 5} more genius picks available</span>
                </div>
            )}
        </motion.div>
    );
};
