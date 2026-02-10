import React from "react";
import { Game } from "../../api";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";
import { Clock, TrendingUp, Sparkles, Brain } from "lucide-react";
import { Link } from "react-router-dom";

interface GameCardProps {
    game: Game;
}

const OddsPill = ({ value, price, type, label }: { value: string | number | null, price: number | null, type: 'spread' | 'total' | 'money', label?: string }) => {
    if (value === null && price === null) return <div className="h-14 bg-white/5 rounded-lg animate-pulse" />;

    return (
        <div className="flex flex-col items-center justify-center bg-white/5 hover:bg-white/10 border border-white/5 hover:border-primary/30 rounded-lg p-2 transition-all cursor-pointer group h-14 relative overflow-hidden">
            {label && (
                <span className="absolute top-1 left-1.5 text-[8px] uppercase text-muted/50 font-bold tracking-tighter">
                    {label}
                </span>
            )}
            <div className="flex items-baseline gap-1 mt-1">
                <span className={cn(
                    "text-sm font-bold",
                    type === 'spread' ? (Number(value) < 0 ? "text-emerald-400" : "text-foreground") : "text-foreground"
                )}>
                    {type === 'spread' && Number(value) > 0 ? "+" : ""}{value}
                </span>
                {price !== null && (
                    <span className="text-[10px] text-muted group-hover:text-primary transition-colors">
                        {price > 0 ? "+" : ""}{price}
                    </span>
                )}
            </div>
        </div>
    );
};

export const GameCard: React.FC<GameCardProps> = ({ game }) => {
    // Merge all odds rows into one complete object, preferring the most recent non-null value for each field
    const odds = (() => {
        if (!game.odds || game.odds.length === 0) return null;

        // Sort newest first
        const sorted = [...game.odds].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

        const merged = { ...sorted[0] };

        // Fill in nulls from older rows
        for (const row of sorted) {
            if (merged.home_moneyline == null) merged.home_moneyline = row.home_moneyline;
            if (merged.away_moneyline == null) merged.away_moneyline = row.away_moneyline;
            if (merged.spread_points == null) merged.spread_points = row.spread_points;
            if (merged.home_spread_price == null) merged.home_spread_price = row.home_spread_price;
            if (merged.away_spread_price == null) merged.away_spread_price = row.away_spread_price;
            if (merged.total_points == null) merged.total_points = row.total_points;
            if (merged.over_price == null) merged.over_price = row.over_price;
            if (merged.under_price == null) merged.under_price = row.under_price;
        }
        return merged;
    })();

    const gameDate = new Date(game.game_date);
    const isToday = gameDate.toDateString() === new Date().toDateString();
    const timeStr = gameDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
    const dateStr = isToday ? "Today" : gameDate.toLocaleDateString([], { month: 'short', day: 'numeric' });
    const displayTime = `${dateStr} ${timeStr}`;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)" }}
            className="bg-card border border-white/5 rounded-2xl p-5 relative overflow-hidden group"
        >
            {/* Background Accent */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 blur-3xl rounded-full -mr-16 -mt-16 group-hover:bg-primary/10 transition-colors" />

            {/* Header */}
            <div className="flex justify-between items-start mb-4 relative z-10">
                <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted">
                        <Clock size={13} />
                        {game.status === "Live" ? (
                            <span className="text-emerald-400 font-bold animate-pulse tabular-nums">
                                {game.quarter} • {game.clock}
                            </span>
                        ) : (
                            <span>{displayTime}</span>
                        )}
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {game.sport && (
                        <span className="text-[10px] font-black tracking-widest text-white/10 uppercase mr-1">{game.sport}</span>
                    )}
                    {game.status === "Live" && (
                        <div className="bg-emerald-500/10 text-emerald-500 text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border border-emerald-500/20 flex items-center gap-1.5 shadow-sm shadow-emerald-500/10">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                            Live
                        </div>
                    )}
                    {game.status === "Final" && (
                        <div className="bg-white/5 text-muted text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border border-white/10">
                            Final
                        </div>
                    )}
                </div>
            </div>

            {/* Teams & Scores */}
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 mb-5 relative z-10">
                <div className="flex flex-col items-start gap-2 overflow-hidden">
                    <div className="flex items-center gap-2 w-full">
                        {game.away_team.logo_url && (
                            <img src={game.away_team.logo_url} alt={game.away_team.name} className="w-8 h-8 object-contain shrink-0" />
                        )}
                        <span className="text-sm font-bold text-white leading-tight line-clamp-2" title={game.away_team.name}>
                            {game.away_team.name}
                        </span>
                    </div>
                </div>

                <div className="flex justify-center min-w-[60px]">
                    {game.status !== "Scheduled" ? (
                        <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg border border-white/5">
                            <span className={`text-xl font-bold tracking-tight ${game.away_score > game.home_score ? 'text-white' : 'text-muted'}`}>{game.away_score}</span>
                            <span className="text-muted text-xs">-</span>
                            <span className={`text-xl font-bold tracking-tight ${game.home_score > game.away_score ? 'text-white' : 'text-muted'}`}>{game.home_score}</span>
                        </div>
                    ) : (
                        <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-muted text-xs font-mono font-bold">@</div>
                    )}
                </div>

                <div className="flex flex-col items-end gap-2 overflow-hidden text-right">
                    <div className="flex flex-row-reverse items-center gap-2 w-full">
                        {game.home_team.logo_url && (
                            <img src={game.home_team.logo_url} alt={game.home_team.name} className="w-8 h-8 object-contain shrink-0" />
                        )}
                        <span className="text-sm font-bold text-white leading-tight line-clamp-2" title={game.home_team.name}>
                            {game.home_team.name}
                        </span>
                    </div>
                </div>
            </div>

            {/* Odds Grid */}
            {odds ? (
                <div className="grid grid-cols-3 gap-2 relative z-10">
                    <div className="col-span-3 grid grid-cols-3 gap-2 mb-1 px-1">
                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">Spread</div>
                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">Total</div>
                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">Money</div>
                    </div>

                    {/* Away Odds */}
                    <OddsPill value={odds.spread_points} price={odds.away_spread_price} type="spread" />
                    <OddsPill label="Over" value={odds.total_points} price={odds.over_price} type="total" />
                    <OddsPill value={odds.away_moneyline} price={null} type="money" />

                    {/* Home Odds */}
                    {/* Convention: spread_points is usually given for the home team or away team. 
                        In our scraper, we store it as is. Usually if +X for away, then -X for home. */}
                    <OddsPill value={odds.spread_points !== null ? -odds.spread_points : null} price={odds.home_spread_price} type="spread" />
                    <OddsPill label="Under" value={odds.total_points} price={odds.under_price} type="total" />
                    <OddsPill value={odds.home_moneyline} price={null} type="money" />

                    {/* Additional Game Props */}
                    {odds.additional_props && (
                        <>
                            {/* First Half Odds */}
                            {odds.additional_props.first_half_home_moneyline !== undefined && (
                                <>
                                    <div className="col-span-3 grid grid-cols-3 gap-2 mb-1 px-1 mt-3">
                                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">1H Spread</div>
                                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">1H Total</div>
                                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">1H Money</div>
                                    </div>
                                    <OddsPill value={odds.additional_props.first_half_spread_points} price={odds.additional_props.first_half_away_spread_price} type="spread" />
                                    <OddsPill label="Over" value={odds.additional_props.first_half_total_points} price={odds.additional_props.first_half_over_price} type="total" />
                                    <OddsPill value={odds.additional_props.first_half_away_moneyline} price={null} type="money" />
                                    <OddsPill value={odds.additional_props.first_half_spread_points !== null ? -odds.additional_props.first_half_spread_points : null} price={odds.additional_props.first_half_home_spread_price} type="spread" />
                                    <OddsPill label="Under" value={odds.additional_props.first_half_total_points} price={odds.additional_props.first_half_under_price} type="total" />
                                    <OddsPill value={odds.additional_props.first_half_home_moneyline} price={null} type="money" />
                                </>
                            )}

                            {/* Odd/Even */}
                            {odds.additional_props.total_points_odd_even !== undefined && (
                                <>
                                    <div className="col-span-3 grid grid-cols-2 gap-2 mb-1 px-1 mt-3">
                                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">Total Odd</div>
                                        <div className="text-[9px] text-center text-muted/60 uppercase tracking-widest font-black">Total Even</div>
                                    </div>
                                    <div className="col-span-2 grid grid-cols-2 gap-2">
                                        <OddsPill value="Odd" price={odds.additional_props.total_points_odd_price} type="total" />
                                        <OddsPill value="Even" price={odds.additional_props.total_points_even_price} type="total" />
                                    </div>
                                </>
                            )}
                        </>
                    )}
                </div>
            ) : (
                <div className="h-28 flex items-center justify-center text-xs text-muted border border-dashed border-white/10 rounded-xl bg-white/5 font-medium">
                    Market Suspended or Unavailable
                </div>
            )}

            {/* Footer / Action */}
            <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center">
                {game.recommendations && game.recommendations.length > 0 ? (
                    <div className="flex items-center gap-2">
                        {game.recommendations[0].reasoning.includes("ML Enhanced") ? (
                             <div className="flex items-center gap-1.5 text-xs font-bold text-purple-400 bg-purple-500/10 px-2 py-1 rounded-lg border border-purple-500/20">
                                <Brain size={12} className="animate-pulse" />
                                <span>AI Pick: {game.recommendations[0].recommended_pick}</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5 text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded-lg border border-primary/20">
                                <Sparkles size={12} className="animate-pulse" />
                                <span>Smart Pick: {game.recommendations[0].recommended_pick}</span>
                            </div>
                        )}
                        
                        <span className={cn(
                            "text-[10px] font-bold px-1.5 py-1 rounded-md border border-white/10",
                            game.recommendations[0].confidence_score > 0.75 ? "text-emerald-400 bg-emerald-400/10" : "text-muted bg-white/5"
                        )}>
                            {(game.recommendations[0].confidence_score * 100).toFixed(0)}%
                        </span>
                    </div>
                ) : (
                    <div className="flex items-center gap-1.5 text-xs text-muted/60">
                        <TrendingUp size={14} className="opacity-50" />
                        <span>Analysis Ready</span>
                    </div>
                )}
                <Link to={`/games/${game.id}`} className="text-xs font-bold text-white hover:text-primary transition-all flex items-center gap-1 group/link">
                    Analyze Matchup
                    <span className="group-hover:translate-x-1 transition-transform">&rarr;</span>
                </Link>
            </div>
        </motion.div>
    );
};
