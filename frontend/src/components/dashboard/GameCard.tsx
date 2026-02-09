import React from "react";
import { Game } from "../../api";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";
import { Clock, TrendingUp } from "lucide-react";
import { Link } from "react-router-dom";

interface GameCardProps {
    game: Game;
}

const OddsPill = ({ value, price, type }: { value: string | number | null, price: number | null, type: 'spread' | 'total' | 'money' }) => {
    if (value === null && price === null) return <div className="h-14 bg-white/5 rounded-lg animate-pulse" />;

    return (
        <div className="flex flex-col items-center justify-center bg-white/5 hover:bg-white/10 border border-white/5 hover:border-primary/30 rounded-lg p-2 transition-all cursor-pointer group h-14">
            {/* <span className="text-[10px] uppercase text-muted font-bold tracking-wider mb-0.5">{label}</span> */}
            <div className="flex items-baseline gap-1">
                <span className={cn("text-sm font-bold text-foreground", type === 'spread' && (Number(value) > 0 ? "text-primary" : "text-white"))}>
                    {value && Number(value) > 0 && type === 'spread' ? "+" : ""}{value}
                </span>
                {price && (
                    <span className="text-[10px] text-muted group-hover:text-primary transition-colors">
                        {price > 0 ? "+" : ""}{price}
                    </span>
                )}
            </div>
        </div>
    );
};

export const GameCard: React.FC<GameCardProps> = ({ game }) => {
    const odds = game.odds[0]; // Display latest odds
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

            {/* Header */}
            <div className="flex justify-between items-start mb-4">
                <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2 text-xs font-medium text-muted">
                        <Clock size={13} />
                        {game.status === "Live" ? (
                            <span className="text-red-500 font-bold animate-pulse tabular-nums">
                                {game.quarter} • {game.clock}
                            </span>
                        ) : (
                            <span>{displayTime}</span>
                        )}
                    </div>
                </div>

                {/* Status & Sport Badge */}
                <div className="flex items-center gap-2">
                    {game.sport && (
                        <span className="text-[10px] font-black tracking-widest text-white/10 uppercase mr-1">{game.sport}</span>
                    )}
                    {game.status === "Live" && (
                        <div className="bg-red-500/10 text-red-500 text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border border-red-500/20 flex items-center gap-1.5 shadow-sm shadow-red-500/10">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
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
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 mb-5">
                {/* Away Team */}
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

                {/* Score vs VS */}
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

                {/* Home Team */}
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
                <div className="grid grid-cols-3 gap-2">
                    {/* Headers */}
                    <div className="col-span-3 grid grid-cols-3 gap-2 mb-1 px-1">
                        <div className="text-[10px] text-center text-muted uppercase tracking-wider font-bold">Spread</div>
                        <div className="text-[10px] text-center text-muted uppercase tracking-wider font-bold">Total</div>
                        <div className="text-[10px] text-center text-muted uppercase tracking-wider font-bold">Money</div>
                    </div>

                    {/* Away Odds */}
                    <OddsPill value={odds.spread_points} price={odds.away_spread_price} type="spread" />
                    <OddsPill value={odds.total_points} price={odds.over_price} type="total" />
                    <OddsPill value={odds.away_moneyline} price={null} type="money" />

                    {/* Home Odds */}
                    <OddsPill value={odds.spread_points ? -odds.spread_points : null} price={odds.home_spread_price} type="spread" />
                    <OddsPill value={odds.total_points} price={odds.under_price} type="total" />
                    <OddsPill value={odds.home_moneyline} price={null} type="money" />
                </div>
            ) : (
                <div className="h-20 flex items-center justify-center text-xs text-muted border border-dashed border-white/10 rounded-xl bg-white/5">
                    Odds Unavailable
                </div>
            )}

            {/* Footer / Action */}
            <div className="mt-4 pt-4 border-t border-white/5 flex justify-between items-center">
                <div className="flex items-center gap-1.5 text-xs text-emerald-400">
                    <TrendingUp size={14} />
                    <span>High Volume</span>
                </div>
                <Link to={`/games/${game.id}`} className="text-xs font-medium text-white hover:text-primary transition-colors">
                    Analyze Matchup &rarr;
                </Link>
            </div>
        </motion.div>
    );
};
