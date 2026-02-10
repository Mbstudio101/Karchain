import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api";
import { RefreshCw, Trophy, TrendingUp, Layers } from "lucide-react";
import { motion } from "framer-motion";

interface ParlayLeg {
    game_id: number;
    pick: string;
    odds: number;
    confidence: number;
}

interface Parlay {
    legs: ParlayLeg[];
    combined_odds: number;
    potential_payout: number;
    confidence_score: number;
}

const LEG_OPTIONS = [3, 5, 6, 8];

export const ParlayCard: React.FC = () => {
    const queryClient = useQueryClient();
    const [selectedLegs, setSelectedLegs] = useState(5);

    const fetchMixedParlay = async (legs: number): Promise<Parlay> => {
        // Add random seed to bypass caching and force fresh generation
        const seed = Math.floor(Math.random() * 1000000);
        const { data } = await api.post<Parlay>(`/recommendations/generate-mixed-parlay?legs=${legs}&seed=${seed}`);
        return data;
    };

    const { data: parlay, isLoading, isError, error } = useQuery({
        queryKey: ["mixedParlay", selectedLegs],
        queryFn: () => fetchMixedParlay(selectedLegs),
        retry: false,
        staleTime: 0, // Force fresh data on each call
        gcTime: 1000 * 60 * 2 // Keep in cache for 2 minutes max
    });

    const regenerateMutation = useMutation({
        mutationFn: () => fetchMixedParlay(selectedLegs),
        onSuccess: (data) => {
            queryClient.setQueryData(["mixedParlay", selectedLegs], data);
        }
    });

    const formatOdds = (odds: number) => (odds > 0 ? `+${odds}` : odds);

    // Determine bet type from pick string
    const getBetType = (pick: string): 'prop' | 'spread' | 'moneyline' => {
        if (pick.includes('OVER') || pick.includes('UNDER')) return 'prop';
        if (pick.includes('Spread')) return 'spread';
        return 'moneyline';
    };

    const getBetTypeColor = (type: 'prop' | 'spread' | 'moneyline') => {
        switch (type) {
            case 'prop': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
            case 'spread': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
            case 'moneyline': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
        }
    };

    const getBetTypeLabel = (type: 'prop' | 'spread' | 'moneyline') => {
        switch (type) {
            case 'prop': return 'PROP';
            case 'spread': return 'SPREAD';
            case 'moneyline': return 'ML';
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-linear-to-br from-accent/20 via-purple-900/20 to-blue-900/20 border border-accent/30 rounded-2xl p-5 relative overflow-hidden h-full flex flex-col"
        >
            <div className="absolute -right-8 -top-8 bg-accent/20 w-32 h-32 rounded-full blur-3xl" />
            <div className="absolute -left-8 -bottom-8 bg-purple-500/10 w-24 h-24 rounded-full blur-2xl" />

            <div className="relative z-10 flex flex-col h-full">
                {/* Header */}
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-accent">
                        <Layers size={16} className="animate-pulse" />
                        <span className="text-xs font-bold uppercase tracking-wider">AI Mixed Parlay</span>
                    </div>
                    <button
                        onClick={() => regenerateMutation.mutate()}
                        disabled={regenerateMutation.isPending}
                        className="text-xs text-accent hover:text-purple-300 transition-colors flex items-center gap-1"
                    >
                        <RefreshCw size={12} className={regenerateMutation.isPending ? "animate-spin" : ""} />
                        Refresh
                    </button>
                </div>

                {/* Leg Selector */}
                <div className="flex gap-1.5 mb-3">
                    {LEG_OPTIONS.map((legs) => (
                        <button
                            key={legs}
                            onClick={() => setSelectedLegs(legs)}
                            className={`flex-1 px-2 py-1.5 rounded-lg text-[10px] font-bold transition-all ${selectedLegs === legs
                                ? "bg-accent text-black"
                                : "bg-white/5 text-muted hover:bg-white/10"
                                }`}
                        >
                            {legs} Legs
                        </button>
                    ))}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {isLoading && (
                        <div className="h-full flex items-center justify-center">
                            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent" />
                        </div>
                    )}

                    {isError && (
                        <div className="text-xs text-muted italic text-center py-4">
                            {(error as any)?.response?.data?.detail || "Generate recommendations first."}
                        </div>
                    )}

                    {parlay && (
                        <div className="flex flex-col h-full">
                            {/* Scrollable Legs */}
                            <div className="flex-1 overflow-y-auto space-y-1.5 mb-3 pr-1" style={{ maxHeight: "200px" }}>
                                {parlay.legs.map((leg, i) => {
                                    const betType = getBetType(leg.pick);
                                    return (
                                        <div key={i} className="bg-white/5 p-2 rounded-lg">
                                            <div className="flex items-start gap-2">
                                                <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded border ${getBetTypeColor(betType)}`}>
                                                    {getBetTypeLabel(betType)}
                                                </span>
                                                <div className="flex-1 min-w-0">
                                                    <div className="text-xs text-white font-medium truncate">{leg.pick}</div>
                                                    <div className="flex items-center gap-2 mt-0.5">
                                                        <span className="text-[10px] font-mono text-muted">{formatOdds(leg.odds)}</span>
                                                        <span className="text-[10px] text-emerald-400">{(leg.confidence * 100).toFixed(0)}%</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Summary Footer */}
                            <div className="border-t border-white/10 pt-3 shrink-0">
                                <div className="flex items-center justify-between mb-2">
                                    <div>
                                        <div className="text-[10px] text-muted mb-0.5">Combined Odds</div>
                                        <div className="text-xl font-black text-accent">{formatOdds(parlay.combined_odds)}</div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-[10px] text-muted mb-0.5">$100 to Win</div>
                                        <div className="text-xl font-black text-white">${parlay.potential_payout.toFixed(0)}</div>
                                    </div>
                                </div>

                                <div className="flex items-center justify-between text-[10px]">
                                    <div className="flex items-center gap-1 text-yellow-400">
                                        <Trophy size={12} />
                                        <span>Confidence: {(parlay.confidence_score * 100).toFixed(0)}%</span>
                                    </div>
                                    <div className="flex items-center gap-1 text-purple-400">
                                        <TrendingUp size={12} />
                                        <span>Props + Games Mix</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
