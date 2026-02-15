import React from "react";
import { Game } from "../../api";
import { cn } from "../../lib/utils";
import { motion } from "framer-motion";
import { Clock, TrendingUp, Sparkles, Brain } from "lucide-react";
import { Link } from "react-router-dom";

interface GameCardProps {
    game: Game;
}

const TEAM_ABBR_BY_NAME: Record<string, string> = {
    "Atlanta Hawks": "atl",
    "Boston Celtics": "bos",
    "Brooklyn Nets": "bkn",
    "Charlotte Hornets": "cha",
    "Chicago Bulls": "chi",
    "Cleveland Cavaliers": "cle",
    "Dallas Mavericks": "dal",
    "Denver Nuggets": "den",
    "Detroit Pistons": "det",
    "Golden State Warriors": "gs",
    "Houston Rockets": "hou",
    "Indiana Pacers": "ind",
    "LA Clippers": "lac",
    "Los Angeles Clippers": "lac",
    "Los Angeles Lakers": "lal",
    "LA Lakers": "lal",
    "Memphis Grizzlies": "mem",
    "Miami Heat": "mia",
    "Milwaukee Bucks": "mil",
    "Minnesota Timberwolves": "min",
    "New Orleans Pelicans": "no",
    "New York Knicks": "ny",
    "Oklahoma City Thunder": "okc",
    "Orlando Magic": "orl",
    "Philadelphia 76ers": "phi",
    "Phoenix Suns": "phx",
    "Portland Trail Blazers": "por",
    "Sacramento Kings": "sac",
    "San Antonio Spurs": "sa",
    "Toronto Raptors": "tor",
    "Utah Jazz": "utah",
    "Washington Wizards": "wsh"
};

const resolveTeamLogoUrl = (name: string, explicitUrl: string | null) => {
    if (explicitUrl && explicitUrl.trim().length > 0) return explicitUrl;
    const abbr = TEAM_ABBR_BY_NAME[name];
    if (!abbr) return null;
    return `https://a.espncdn.com/i/teamlogos/nba/500/scoreboard/${abbr}.png`;
};

const teamInitials = (name: string) =>
    name
        .split(" ")
        .filter(Boolean)
        .slice(-2)
        .map((p) => p[0]?.toUpperCase() || "")
        .join("");

const TeamBadge = ({ logoUrl, name }: { logoUrl: string | null; name: string }) => {
    const [imgFailed, setImgFailed] = React.useState(false);
    const resolvedLogoUrl = resolveTeamLogoUrl(name, logoUrl);

    if (resolvedLogoUrl && !imgFailed) {
        return (
            <img
                src={resolvedLogoUrl}
                alt={name}
                className="w-9 h-9 object-contain shrink-0"
                onError={() => setImgFailed(true)}
            />
        );
    }

    return (
        <div className="w-9 h-9 rounded-full shrink-0 bg-white/10 border border-white/20 flex items-center justify-center text-[11px] font-black text-white/90">
            {teamInitials(name)}
        </div>
    );
};

const OddsPill = ({ value, price, type, label }: { value: string | number | null, price: number | null, type: 'spread' | 'total' | 'money', label?: string }) => {
    if (value === null && price === null) return <div className="h-14 bg-white/5 rounded-lg animate-pulse border border-white/10" />;

    return (
        <div className="flex flex-col items-center justify-center bg-white/5 hover:bg-white/10 border border-white/10 hover:border-secondary/35 rounded-lg p-2 transition-all group min-h-16 relative overflow-hidden">
            {label && (
                <span className="text-[9px] uppercase text-muted/75 font-black tracking-wide mb-0.5">
                    {label}
                </span>
            )}
            <div className="flex flex-col items-center leading-tight">
                <span className={cn(
                    "text-sm font-bold",
                    type === 'spread' ? (Number(value) < 0 ? "text-primary" : "text-foreground") : "text-foreground"
                )}>
                    {type === 'spread' && Number(value) > 0 ? "+" : ""}{value}
                </span>
                {price !== null && (
                    <span className="text-[10px] text-muted group-hover:text-primary transition-colors mt-0.5">
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
            className="bg-linear-to-br from-[#0f1838] via-card to-[#0b1330] border border-white/10 rounded-2xl p-4 md:p-5 relative overflow-hidden group"
        >
            {/* Background Accent */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-secondary/10 blur-3xl rounded-full -mr-16 -mt-16 group-hover:bg-secondary/20 transition-colors" />
            <div className="absolute bottom-0 left-0 w-24 h-24 bg-primary/10 blur-2xl rounded-full -ml-10 -mb-10 group-hover:bg-primary/20 transition-colors" />

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
                        <div className="bg-primary/10 text-primary text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wider border border-primary/25 flex items-center gap-1.5 shadow-sm shadow-primary/15">
                            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
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
            <div className="mb-5 relative z-10">
                <div className="rounded-xl bg-black/20 border border-white/10 p-2.5 md:p-3">
                    <div className="grid grid-cols-[1fr_auto] items-center gap-3">
                        <div className="min-w-0 flex items-center gap-2.5">
                            <TeamBadge logoUrl={game.away_team.logo_url} name={game.away_team.name} />
                            <div className="min-w-0">
                                <div className="text-[11px] uppercase tracking-wider text-muted/70 font-semibold">Away</div>
                                <div className="text-sm font-bold text-white truncate" title={game.away_team.name}>
                                    {game.away_team.name}
                                </div>
                            </div>
                        </div>
                        <div className={cn(
                            "text-2xl font-black tabular-nums tracking-tight min-w-[2ch] text-right",
                            game.status !== "Scheduled" && game.away_score > game.home_score ? "text-white" : "text-muted"
                        )}>
                            {game.status !== "Scheduled" ? game.away_score : "-"}
                        </div>
                    </div>

                    <div className="flex items-center justify-center py-1.5">
                        <div className="text-[11px] font-bold uppercase tracking-[0.22em] text-muted/65">
                            {game.status === "Scheduled" ? "VS" : "Final Score"}
                        </div>
                    </div>

                    <div className="grid grid-cols-[1fr_auto] items-center gap-3">
                        <div className="min-w-0 flex items-center gap-2.5">
                            <TeamBadge logoUrl={game.home_team.logo_url} name={game.home_team.name} />
                            <div className="min-w-0">
                                <div className="text-[11px] uppercase tracking-wider text-muted/70 font-semibold">Home</div>
                                <div className="text-sm font-bold text-white truncate" title={game.home_team.name}>
                                    {game.home_team.name}
                                </div>
                            </div>
                        </div>
                        <div className={cn(
                            "text-2xl font-black tabular-nums tracking-tight min-w-[2ch] text-right",
                            game.status !== "Scheduled" && game.home_score > game.away_score ? "text-white" : "text-muted"
                        )}>
                            {game.status !== "Scheduled" ? game.home_score : "-"}
                        </div>
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
                    <div className="col-span-3 text-[10px] font-black uppercase tracking-wider text-muted/75 px-1 mt-0.5">
                        Away
                    </div>
                    <OddsPill value={odds.spread_points} price={odds.away_spread_price} type="spread" />
                    <OddsPill label="Over" value={odds.total_points} price={odds.over_price} type="total" />
                    <OddsPill value={odds.away_moneyline} price={null} type="money" />

                    {/* Home Odds */}
                    <div className="col-span-3 text-[10px] font-black uppercase tracking-wider text-muted/75 px-1 mt-1">
                        Home
                    </div>
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
                        {(game.recommendations[0].reasoning || "").includes("ML Enhanced") ? (
                             <div className="flex items-center gap-1.5 text-xs font-bold text-accent bg-accent/10 px-2 py-1 rounded-lg border border-accent/25">
                                <Brain size={12} className="animate-pulse" />
                                <span>AI Pick: {game.recommendations[0].recommended_pick}</span>
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5 text-xs font-bold text-secondary bg-secondary/10 px-2 py-1 rounded-lg border border-secondary/25">
                                <Sparkles size={12} className="animate-pulse" />
                                <span>Smart Pick: {game.recommendations[0].recommended_pick}</span>
                            </div>
                        )}
                        
                        <span className={cn(
                            "text-[10px] font-bold px-1.5 py-1 rounded-md border border-white/10",
                            game.recommendations[0].confidence_score > 0.75 ? "text-primary bg-primary/10" : "text-muted bg-white/5"
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
