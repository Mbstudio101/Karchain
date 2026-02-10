import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { History as HistoryIcon, TrendingUp, TrendingDown, Clock, ExternalLink } from "lucide-react";
import { motion } from "framer-motion";

interface Recommendation {
    id: number;
    game_id: number;
    bet_type: string;
    recommended_pick: string;
    confidence_score: number;
    reasoning: string | null;
    timestamp: string;
}

const fetchBetHistory = async (): Promise<Recommendation[]> => {
    const { data } = await api.get<Recommendation[]>("/recommendations/");
    return data;
};

export const History: React.FC = () => {
    const navigate = useNavigate();
    const { data: bets, isLoading } = useQuery({
        queryKey: ["betHistory"],
        queryFn: fetchBetHistory
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
        );
    }

    // Calculate summary stats
    const totalBets = bets?.length || 0;
    const highConfidence = bets?.filter(b => b.confidence_score >= 0.7).length || 0;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <HistoryIcon size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Recommendation History</h1>
                        <p className="text-xs text-muted">All AI-generated picks from market analysis</p>
                    </div>
                </div>

                <div className="flex gap-4">
                    <div className="bg-white/5 rounded-lg px-4 py-2 text-center">
                        <div className="text-lg font-bold text-white">{totalBets}</div>
                        <div className="text-[10px] text-muted uppercase">Total Picks</div>
                    </div>
                    <div className="bg-emerald-500/10 rounded-lg px-4 py-2 text-center border border-emerald-500/20">
                        <div className="text-lg font-bold text-emerald-400">{highConfidence}</div>
                        <div className="text-[10px] text-emerald-400/70 uppercase">High Conf</div>
                    </div>
                </div>
            </div>

            <div className="bg-card border border-white/5 rounded-2xl overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-white/5 text-xs text-muted uppercase tracking-wider">
                            <th className="p-4 font-medium">Date</th>
                            <th className="p-4 font-medium">Type</th>
                            <th className="p-4 font-medium">Pick</th>
                            <th className="p-4 font-medium">Confidence</th>
                            <th className="p-4 font-medium">Reasoning</th>
                            <th className="p-4 font-medium w-10"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {bets?.length === 0 && (
                            <tr>
                                <td colSpan={6} className="p-8 text-center text-muted">
                                    No recommendations yet. Go to Dashboard and click "Scan Market" to generate picks.
                                </td>
                            </tr>
                        )}
                        {bets?.map((bet, i) => (
                            <motion.tr
                                key={bet.id}
                                initial={{ opacity: 0, y: 5 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.03 }}
                                onClick={() => navigate(`/games/${bet.game_id}`)}
                                className="hover:bg-white/5 transition-colors cursor-pointer"
                            >
                                <td className="p-4 text-sm text-muted">
                                    <div className="flex items-center gap-2">
                                        <Clock size={12} />
                                        {new Date(bet.timestamp).toLocaleDateString()}
                                    </div>
                                </td>
                                <td className="p-4">
                                    <span className="text-xs font-bold px-2 py-1 rounded bg-primary/10 text-primary uppercase">
                                        {bet.bet_type}
                                    </span>
                                </td>
                                <td className="p-4 text-sm font-medium text-white">{bet.recommended_pick}</td>
                                <td className="p-4">
                                    <div className="flex items-center gap-2">
                                        {bet.confidence_score >= 0.7 ? (
                                            <TrendingUp size={14} className="text-emerald-400" />
                                        ) : (
                                            <TrendingDown size={14} className="text-yellow-400" />
                                        )}
                                        <span className={`text-sm font-bold ${bet.confidence_score >= 0.7 ? 'text-emerald-400' : 'text-yellow-400'}`}>
                                            {(bet.confidence_score * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                </td>
                                <td className="p-4 text-xs text-muted max-w-xs truncate">
                                    {bet.reasoning || "Automated analysis"}
                                </td>
                                <td className="p-4">
                                    <ExternalLink size={12} className="text-muted" />
                                </td>
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
