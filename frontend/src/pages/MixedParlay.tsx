import React, { useState, useEffect, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchMixedParlay } from "../api";
import { Layers, RefreshCw, Trophy, TrendingUp, Zap, Target, Brain } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAvailableDates } from "../hooks/useAvailableDates";
import { getLocalISODate } from "../lib/utils";

const getBetType = (pick: string): 'prop' | 'spread' | 'moneyline' => {
    if (pick.includes('OVER') || pick.includes('UNDER')) return 'prop';
    if (pick.includes('Spread')) return 'spread';
    return 'moneyline';
};

const getBetTypeLabel = (type: 'prop' | 'spread' | 'moneyline'): string => {
    return { prop: 'PROP', spread: 'SPREAD', moneyline: 'ML' }[type];
};

const getBetTypeColor = (type: 'prop' | 'spread' | 'moneyline'): string => {
    return {
        prop: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
        spread: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        moneyline: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    }[type];
};

type ParsedLegPick = {
    title: string;
    market: string | null;
    side: "OVER" | "UNDER" | null;
    line: string | null;
    subtitle: string;
};

const normalizeMarket = (market: string) => {
    const map: Record<string, string> = {
        "PTS+REB+AST": "PTS + REB + AST",
        "PTS+REB": "PTS + REB",
        "PTS+AST": "PTS + AST",
        "REB+AST": "REB + AST",
    };
    const upper = market.toUpperCase();
    return map[upper] || upper.replace(/\+/g, " + ");
};

const parseLegPick = (pick: string, type: 'prop' | 'spread' | 'moneyline'): ParsedLegPick => {
    if (type !== "prop") {
        return {
            title: pick,
            market: null,
            side: null,
            line: null,
            subtitle: "Game market leg",
        };
    }

    const match = pick.match(/^(.*?)\s+([A-Z0-9+]+)\s+(OVER|UNDER)\s+(-?\d+(?:\.\d+)?)$/i);
    if (!match) {
        return {
            title: pick,
            market: null,
            side: null,
            line: null,
            subtitle: "Player prop leg",
        };
    }

    const [, player, market, side, line] = match;
    return {
        title: player.trim(),
        market: normalizeMarket(market.trim()),
        side: side.toUpperCase() as "OVER" | "UNDER",
        line,
        subtitle: "Player prop leg",
    };
};

export const MixedParlay: React.FC = () => {
    const queryClient = useQueryClient();
    const [selectedLegs, setSelectedLegs] = useState(5);
    const [stake, setStake] = useState(100);
    const { availableDates, defaultDate } = useAvailableDates();
    const [selectedDate, setSelectedDate] = useState(() => {
        return defaultDate || getLocalISODate();
    });

    useEffect(() => {
        if (defaultDate) {
            setSelectedDate(defaultDate);
        }
    }, [defaultDate]);

    const displayedDates = useMemo(() => (
        availableDates.includes(selectedDate) ? availableDates : [selectedDate, ...availableDates]
    ), [availableDates, selectedDate]);

    const { data: parlay, isLoading } = useQuery({
        queryKey: ["mixedParlay", selectedLegs, selectedDate],
        queryFn: () => fetchMixedParlay(selectedLegs, "balanced", selectedDate),
        staleTime: 1000 * 60 * 2,
        enabled: !!selectedDate // Only run query when date is available
    });

    useEffect(() => {
        if (parlay?.date_used && parlay.date_used !== selectedDate) {
            setSelectedDate(parlay.date_used);
        }
    }, [parlay?.date_used, selectedDate]);

    const generateMutation = useMutation({
        mutationFn: (legs: number) => fetchMixedParlay(legs, "balanced", selectedDate),
        onSuccess: (data) => {
            queryClient.setQueryData(["mixedParlay", selectedLegs, selectedDate], data);
        }
    });

    const handleGenerate = () => {
        generateMutation.mutate(selectedLegs);
    };

    const formatOdds = (odds: number) => {
        return odds > 0 ? `+${odds}` : odds.toString();
    };

    const potentialProfit = parlay ? (stake * (parlay.potential_payout / 100 - 1)).toFixed(2) : "0";

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-3 bg-linear-to-br from-purple-500/20 to-indigo-500/20 rounded-xl">
                        <Layers className="text-purple-400" size={28} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">AI Mixed Parlay</h1>
                        <p className="text-sm text-muted">Kelly-optimized player props + game bets</p>
                    </div>
                </div>
                
                <div className="flex items-center gap-2">
                    <select
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm font-medium outline-none focus:border-purple-500/50 transition-colors"
                    >
                        {displayedDates.length > 0 ? (
                            displayedDates.map(date => (
                                <option key={date} value={date} className="bg-card">
                                    {new Date(date).toLocaleDateString('en-US', { 
                                        month: 'short', 
                                        day: 'numeric',
                                        year: 'numeric'
                                    })}
                                </option>
                            ))
                        ) : (
                            <option value={selectedDate} className="bg-card">{selectedDate}</option>
                        )}
                    </select>
                </div>
            </div>

            {/* Controls */}
            <div className="bg-card border border-white/10 rounded-2xl p-6">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    {/* Leg Selector */}
                    <div>
                        <label className="text-xs text-muted uppercase tracking-wider block mb-2">Parlay Size</label>
                        <div className="flex gap-2">
                            {[3, 5, 6, 8].map(num => (
                                <button
                                    key={num}
                                    onClick={() => setSelectedLegs(num)}
                                    className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${selectedLegs === num
                                        ? 'bg-purple-500 text-white'
                                        : 'bg-white/5 text-muted hover:bg-white/10'
                                        }`}
                                >
                                    {num}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Stake Input */}
                    <div>
                        <label className="text-xs text-muted uppercase tracking-wider block mb-2">Stake ($)</label>
                        <input
                            type="number"
                            value={stake}
                            onChange={(e) => setStake(Number(e.target.value))}
                            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white outline-none focus:border-purple-500"
                        />
                    </div>

                    {/* Potential Payout */}
                    <div>
                        <label className="text-xs text-muted uppercase tracking-wider block mb-2">To Win</label>
                        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-4 py-2">
                            <span className="text-2xl font-bold text-emerald-400">${potentialProfit}</span>
                        </div>
                    </div>

                    {/* Generate Button */}
                    <div className="flex items-end">
                        <button
                            onClick={handleGenerate}
                            disabled={generateMutation.isPending}
                            className="w-full flex items-center justify-center gap-2 bg-linear-to-r from-purple-500 to-indigo-500 text-white font-bold py-3 px-6 rounded-xl hover:from-purple-400 hover:to-indigo-400 transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50"
                        >
                            {generateMutation.isPending ? (
                                <RefreshCw className="animate-spin" size={18} />
                            ) : (
                                <Brain size={18} />
                            )}
                            Generate Parlay
                        </button>
                    </div>
                </div>
            </div>

            {/* Parlay Display */}
            {isLoading ? (
                <div className="flex justify-center p-12">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-400" />
                </div>
            ) : parlay ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Parlay Legs */}
                    <div className="lg:col-span-2 space-y-4">
                        <div className="flex items-center justify-between">
                            <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                <Target size={18} className="text-purple-400" />
                                Parlay Legs
                            </h2>
                            <span className="text-xs text-muted">{parlay.legs.length} selections</span>
                        </div>

                        <div className="space-y-3">
                            <AnimatePresence>
                                {parlay.legs.map((leg, i) => {
                                    const betType = getBetType(leg.pick);
                                    const parsed = parseLegPick(leg.pick, betType);
                                    const confidencePct = Math.max(0, Math.min(100, Math.round(leg.confidence * 100)));
                                    return (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 20 }}
                                            transition={{ delay: i * 0.05 }}
                                            className="bg-linear-to-br from-[#0f1b40] to-[#0b1430] border border-white/10 rounded-xl p-4 hover:border-purple-500/35 transition-all"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="min-w-0 flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <span className="text-[10px] font-bold px-2 py-0.5 rounded border text-white/60 border-white/20">
                                                            #{String(i + 1).padStart(2, "0")}
                                                        </span>
                                                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${getBetTypeColor(betType)}`}>
                                                            {getBetTypeLabel(betType)}
                                                        </span>
                                                    </div>

                                                    <div className="text-base font-bold text-white truncate">{parsed.title}</div>

                                                    {parsed.market && parsed.side && parsed.line ? (
                                                        <div className="mt-1 flex flex-wrap items-center gap-2">
                                                            <span className="text-xs text-muted">{parsed.market}</span>
                                                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${parsed.side === "OVER" ? "bg-emerald-500/20 text-emerald-300" : "bg-rose-500/20 text-rose-300"}`}>
                                                                {parsed.side}
                                                            </span>
                                                            <span className="text-sm font-semibold text-secondary">{parsed.line}</span>
                                                        </div>
                                                    ) : (
                                                        <div className="mt-1 text-xs text-muted">{parsed.subtitle}</div>
                                                    )}

                                                    {(leg.opponent || leg.matchup) && (
                                                        <div className="mt-1 text-[11px] text-secondary/90 font-medium">
                                                            {leg.opponent ? `vs ${leg.opponent}` : leg.matchup}
                                                        </div>
                                                    )}

                                                    <div className="mt-3">
                                                        <div className="flex items-center justify-between text-[11px] text-muted mb-1">
                                                            <span>Confidence</span>
                                                            <span className="text-purple-300 font-semibold">{confidencePct}%</span>
                                                        </div>
                                                        <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                                                            <div
                                                                className="h-full bg-linear-to-r from-purple-400 to-indigo-400"
                                                                style={{ width: `${confidencePct}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                </div>

                                                <div className="shrink-0 flex items-start gap-3">
                                                    {betType === "prop" && (
                                                        leg.player_headshot ? (
                                                            <img
                                                                src={leg.player_headshot}
                                                                alt={leg.player_name || parsed.title}
                                                                className="w-12 h-12 rounded-xl object-cover border border-white/15 bg-white/5"
                                                                onError={(e) => {
                                                                    (e.currentTarget as HTMLImageElement).style.display = "none";
                                                                }}
                                                            />
                                                        ) : (
                                                            <div className="w-12 h-12 rounded-xl border border-white/15 bg-white/5 flex items-center justify-center text-xs font-bold text-white/70">
                                                                {(leg.player_name || parsed.title || "?").split(" ").map(s => s[0]).join("").slice(0, 2).toUpperCase()}
                                                            </div>
                                                        )
                                                    )}
                                                    <div className="text-right min-w-[90px]">
                                                    <div className="text-[10px] text-muted uppercase tracking-wide mb-1">Odds</div>
                                                    <div className={`text-xl font-black ${leg.odds > 0 ? 'text-emerald-400' : 'text-white'}`}>
                                                        {formatOdds(leg.odds)}
                                                    </div>
                                                    <div className="mt-2 text-[11px] text-muted">Game #{leg.game_id}</div>
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </AnimatePresence>
                        </div>
                    </div>

                    {/* Summary Card */}
                    <div className="space-y-4">
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-linear-to-br from-purple-900/40 to-indigo-900/40 border border-purple-500/30 rounded-2xl p-6"
                        >
                            <div className="flex items-center gap-2 mb-4">
                                <Trophy className="text-yellow-400" size={20} />
                                <h3 className="font-bold text-white">Parlay Summary</h3>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center justify-between py-3 border-b border-white/10">
                                    <span className="text-muted">Combined Odds</span>
                                    <span className="text-2xl font-bold text-white">{formatOdds(parlay.combined_odds)}</span>
                                </div>

                                <div className="flex items-center justify-between py-3 border-b border-white/10">
                                    <span className="text-muted">Your Stake</span>
                                    <span className="text-xl font-bold text-white">${stake}</span>
                                </div>

                                <div className="flex items-center justify-between py-3 border-b border-white/10">
                                    <span className="text-muted">Potential Payout</span>
                                    <span className="text-xl font-bold text-emerald-400">${(stake * parlay.potential_payout / 100).toFixed(2)}</span>
                                </div>

                                <div className="flex items-center justify-between py-3">
                                    <span className="text-muted">AI Confidence</span>
                                    <div className="flex items-center gap-2">
                                        <TrendingUp size={14} className="text-purple-400" />
                                        <span className="text-xl font-bold text-purple-400">{(parlay.confidence_score * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>
                        </motion.div>

                        {/* Tips */}
                        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                            <h4 className="text-sm font-bold text-white mb-2 flex items-center gap-2">
                                <Zap size={14} className="text-yellow-400" />
                                Pro Tips
                            </h4>
                            <ul className="text-xs text-muted space-y-1">
                                <li>• Purple badges = Player Props (higher variance)</li>
                                <li>• Blue badges = Spread Bets (stable picks)</li>
                                <li>• Green badges = Moneyline (safest)</li>
                                <li>• Mix of bet types reduces correlation</li>
                            </ul>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="text-center py-12 text-muted">
                    Click "Generate Parlay" to create your AI-optimized mixed parlay
                </div>
            )}
        </div>
    );
};
