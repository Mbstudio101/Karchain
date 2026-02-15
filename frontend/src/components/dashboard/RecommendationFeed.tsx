import React from "react";
import { useRecommendations, useGenerateRecommendations } from "../../hooks/useGames";
import { Sparkles, RefreshCw, Brain, Activity } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { Recommendation } from "../../api";
import { cn } from "../../lib/utils";

export const RecommendationFeed: React.FC = () => {
    const { data: recs } = useRecommendations();
    const generateMutation = useGenerateRecommendations();
    const navigate = useNavigate();

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-linear-to-br from-[#13234d] via-[#0f1d41] to-[#0a1534] border border-secondary/25 rounded-2xl p-6 relative overflow-hidden group shadow-[0_20px_40px_-22px_rgba(211,170,74,0.45)]"
            >
                <div className="relative z-10">
                    <div className="flex items-center gap-2 text-secondary mb-2">
                        <Sparkles size={18} className="animate-pulse" />
                        <span className="text-sm font-bold uppercase tracking-[0.18em]">High Roller Signal</span>
                    </div>
                    <h3 className="text-3xl font-black text-white mb-2">{recs?.length || 0} Value Bets</h3>
                    <p className="text-sm text-slate-300/85 mb-4">Live board edges detected from your analytics engine and market movement.</p>

                    <button
                        onClick={() => generateMutation.mutate()}
                        disabled={generateMutation.isPending}
                        className="px-5 py-2.5 bg-linear-to-r from-secondary to-amber-300 text-slate-900 text-sm font-black rounded-xl hover:brightness-110 transition-all flex items-center gap-2 shadow-lg shadow-secondary/35 active:scale-95"
                    >
                        {generateMutation.isPending ? <RefreshCw className="animate-spin" size={16} /> : "Scan Market"}
                    </button>
                </div>
                <div className="absolute -right-12 -bottom-12 bg-secondary/20 w-48 h-48 rounded-full blur-3xl group-hover:bg-secondary/30 transition-colors duration-500" />
            </motion.div>

            {/* Recs List */}
            <div className="col-span-2 bg-card/70 backdrop-blur-sm border border-white/10 rounded-2xl p-6 relative shadow-[0_14px_30px_-20px_rgba(12,18,45,0.8)]">
                <div className="absolute top-0 right-0 p-6">
                    <button
                        onClick={() => navigate("/mixed-parlay")}
                        className="text-xs font-semibold text-secondary hover:text-amber-300 transition-colors"
                    >
                        View All Analysis &rarr;
                    </button>
                </div>
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-secondary" />
                    Top Recommendations
                </h3>
                <div className="space-y-3">
                    {recs?.slice(0, 2).map((rec: Recommendation, i: number) => {
                        const reasoning = rec.reasoning || "Automated analysis";
                        const isML = reasoning.includes("ML Enhanced");
                        const isInjury = reasoning.includes("injury adjustment");
                        const confidenceColor = rec.confidence_score > 0.75 ? "text-emerald-400" : 
                                              rec.confidence_score > 0.60 ? "text-yellow-400" : "text-muted";
                        
                        return (
                        <motion.div
                            key={rec.id}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                            onClick={() => navigate(`/games/${rec.game_id}`)}
                            className="flex items-center justify-between bg-white/5 hover:bg-white/10 p-4 rounded-xl border border-transparent hover:border-secondary/25 transition-colors cursor-pointer group/item relative"
                        >
                            <div className="flex items-center gap-4">
                                <div className={cn("p-2 rounded-lg", isML ? "bg-accent/20 text-accent" : "bg-primary/10 text-primary")}>
                                    {isML ? <Brain size={16} /> : <Sparkles size={16} />}
                                </div>
                                <div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-secondary font-bold uppercase bg-secondary/15 px-1.5 py-0.5 rounded border border-secondary/30">{rec.bet_type}</span>
                                        <span className="text-sm font-medium text-white">{rec.recommended_pick}</span>
                                        {isInjury && (
                                            <div className="flex items-center gap-1 text-[10px] text-orange-400 bg-orange-400/10 px-1.5 py-0.5 rounded border border-orange-400/20" title="Adjusted for significant injuries">
                                                <Activity size={10} />
                                                <span>Injuries</span>
                                            </div>
                                        )}
                                    </div>
                                            <div className="group/tooltip relative">
                                                <span className="text-xs text-muted mt-1 block max-w-sm truncate group-hover/tooltip:text-white transition-colors">
                                            {reasoning}
                                        </span>
                                        {/* Tooltip for full reasoning */}
                                        <div className="absolute left-0 -bottom-2 translate-y-full opacity-0 group-hover/tooltip:opacity-100 pointer-events-none bg-black/90 border border-white/10 p-2 rounded-lg text-xs text-gray-300 w-64 z-50 shadow-xl transition-opacity">
                                            {reasoning}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="text-right">
                                <span className="text-xs text-muted block">Confidence</span>
                                <span className={cn("text-xl font-bold tracking-tight", confidenceColor)}>
                                    {(rec.confidence_score * 100).toFixed(0)}%
                                </span>
                            </div>
                        </motion.div>
                    )})}
                    {!recs?.length && (
                        <div className="text-muted text-sm italic flex flex-col items-center justify-center h-24 text-center">
                            <span>No recommendations generated yet.</span>
                            <span className="text-xs opacity-50">Click "Scan Market" to analyze live odds.</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
