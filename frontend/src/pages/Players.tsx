import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Users, Search, RotateCw, Award, DollarSign, Zap, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

interface PlayerStats {
    points: number;
    rebounds: number;
    assists: number;
    steals?: number;
    blocks?: number;
    minutes_played?: number;
    game_date?: string;
    opponent?: string;
}

interface PlayerProp {
    id: number;
    prop_type: string;
    line: number;
    over_odds: number;
    under_odds: number;
}

interface Player {
    id: number;
    name: string;
    position: string | null;
    sport: string;
    team_id: number | null;
    headshot_url: string | null;
    stats: PlayerStats[];
}

const fetchPlayers = async () => {
    const { data } = await api.get<Player[]>("/players/");
    return data;
};

const fetchPlayerProps = async (playerId: number) => {
    const { data } = await api.get<PlayerProp[]>(`/players/${playerId}/props`);
    return data;
};

const formatOdds = (odds: number) => (odds > 0 ? `+${odds}` : `${odds}`);

// Calculate hit rate for a prop based on historical stats
const calculateHitRate = (stats: PlayerStats[], propType: string, line: number): number => {
    if (!stats.length) return 0;

    const key = propType === 'pts+reb+ast' ? null : propType as keyof PlayerStats;
    let hits = 0;

    for (const stat of stats) {
        let value = 0;
        if (propType === 'pts+reb+ast') {
            value = (stat.points || 0) + (stat.rebounds || 0) + (stat.assists || 0);
        } else if (key && stat[key] !== undefined) {
            value = Number(stat[key]) || 0;
        }
        if (value > line) hits++;
    }

    return (hits / stats.length) * 100;
};

// Flip Card Component
const PlayerFlipCard: React.FC<{ player: Player; index: number; selectedPicks: Record<string, 'over' | 'under'>; onTogglePick: (key: string, side: 'over' | 'under') => void }> = ({ player, index, selectedPicks, onTogglePick }) => {
    const [isFlipped, setIsFlipped] = useState(false);

    const { data: props } = useQuery({
        queryKey: ["playerProps", player.id],
        queryFn: () => fetchPlayerProps(player.id),
        enabled: isFlipped,
        staleTime: 1000 * 60 * 5
    });

    const getAvg = (key: keyof PlayerStats) => {
        const validStats = player.stats.filter(s => s[key] !== undefined && s[key] !== null);
        if (!validStats.length) return "0.0";
        const sum = validStats.reduce((acc, s) => acc + (Number(s[key]) || 0), 0);
        return (sum / validStats.length).toFixed(1);
    };

    const getMax = (key: keyof PlayerStats) => {
        const validStats = player.stats.filter(s => s[key] !== undefined && s[key] !== null);
        if (!validStats.length) return 0;
        return Math.max(...validStats.map(s => Number(s[key]) || 0));
    };

    const lastGame = player.stats.length > 0 ? player.stats[0] : null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.02 }}
            className="relative h-[420px] cursor-pointer"
            style={{ perspective: "1000px" }}
            onClick={() => setIsFlipped(!isFlipped)}
        >
            <motion.div
                animate={{ rotateY: isFlipped ? 180 : 0 }}
                transition={{ duration: 0.5, type: "spring", stiffness: 100 }}
                className="relative w-full h-full"
                style={{ transformStyle: "preserve-3d" }}
            >
                {/* FRONT OF CARD */}
                <div
                    className="absolute inset-0 bg-card border border-white/10 rounded-2xl p-4 overflow-hidden"
                    style={{ backfaceVisibility: "hidden" }}
                >
                    {/* Header */}
                    <div className="flex items-start gap-3 mb-3">
                        <div className="w-14 h-14 rounded-full bg-gradient-to-br from-primary/20 to-primary/5 overflow-hidden flex-shrink-0 ring-2 ring-primary/30">
                            {player.headshot_url ? (
                                <img src={player.headshot_url} alt={player.name} className="w-full h-full object-cover" />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-xl font-bold text-primary">
                                    {player.name.charAt(0)}
                                </div>
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-white text-sm leading-tight" title={player.name}>{player.name}</h3>
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-muted">{player.position || "N/A"}</span>
                                <span className="text-[9px] bg-primary/20 text-primary px-1.5 py-0.5 rounded">{player.sport}</span>
                            </div>
                        </div>
                    </div>

                    {/* Main Stats */}
                    <div className="grid grid-cols-3 gap-2 mb-3">
                        <div className="bg-white/5 rounded-lg p-2 text-center">
                            <div className="text-lg font-bold text-white">{getAvg('points')}</div>
                            <div className="text-[9px] text-muted uppercase">PPG</div>
                        </div>
                        <div className="bg-white/5 rounded-lg p-2 text-center">
                            <div className="text-lg font-bold text-white">{getAvg('rebounds')}</div>
                            <div className="text-[9px] text-muted uppercase">RPG</div>
                        </div>
                        <div className="bg-white/5 rounded-lg p-2 text-center">
                            <div className="text-lg font-bold text-white">{getAvg('assists')}</div>
                            <div className="text-[9px] text-muted uppercase">APG</div>
                        </div>
                    </div>

                    {/* Season Highs */}
                    <div className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border border-yellow-500/20 rounded-lg p-2 mb-3">
                        <div className="flex items-center gap-1 text-[10px] text-yellow-400 mb-1">
                            <Award size={10} />
                            <span className="uppercase font-bold">Season Highs</span>
                        </div>
                        <div className="grid grid-cols-3 gap-2 text-center">
                            <div>
                                <span className="text-sm font-bold text-white">{getMax('points')}</span>
                                <span className="text-[8px] text-muted ml-1">PTS</span>
                            </div>
                            <div>
                                <span className="text-sm font-bold text-white">{getMax('rebounds')}</span>
                                <span className="text-[8px] text-muted ml-1">REB</span>
                            </div>
                            <div>
                                <span className="text-sm font-bold text-white">{getMax('assists')}</span>
                                <span className="text-[8px] text-muted ml-1">AST</span>
                            </div>
                        </div>
                    </div>

                    {/* Last Game */}
                    {lastGame && (
                        <div className="bg-white/5 rounded-lg p-2 mb-3">
                            <div className="flex items-center gap-1 text-[10px] text-emerald-400 mb-1">
                                <Zap size={10} />
                                <span className="uppercase font-bold">Last: vs {lastGame.opponent || "OPP"}</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-white font-bold">{lastGame.points?.toFixed(0)} PTS</span>
                                <span className="text-white font-bold">{lastGame.rebounds?.toFixed(0)} REB</span>
                                <span className="text-white font-bold">{lastGame.assists?.toFixed(0)} AST</span>
                            </div>
                        </div>
                    )}

                    {/* Trend */}
                    <div className="flex items-center gap-2 text-xs text-primary mb-2">
                        <TrendingUp size={12} />
                        <span>{player.stats.length} games tracked</span>
                    </div>

                    {/* Flip Hint */}
                    <div className="absolute bottom-3 left-0 right-0 text-center">
                        <div className="inline-flex items-center gap-1 text-[10px] text-muted/50 bg-white/5 px-2 py-1 rounded-full">
                            <RotateCw size={10} />
                            <span>Tap for betting props</span>
                        </div>
                    </div>
                </div>

                {/* BACK OF CARD - PROPS */}
                <div
                    className="absolute inset-0 bg-gradient-to-br from-slate-900 to-card border border-primary/40 rounded-2xl flex flex-col overflow-hidden"
                    style={{ backfaceVisibility: "hidden", transform: "rotateY(180deg)" }}
                >
                    {/* Header - Fixed */}
                    <div className="flex items-center justify-between p-3 border-b border-white/10 flex-shrink-0">
                        <div className="flex items-center gap-2">
                            <DollarSign size={14} className="text-primary" />
                            <span className="font-bold text-primary text-xs uppercase tracking-wider">Player Props</span>
                        </div>
                        <span className="text-[10px] text-muted truncate max-w-20">{player.name}</span>
                    </div>

                    {/* Scrollable Props Area */}
                    <div className="flex-1 overflow-y-auto p-3 space-y-2" style={{ maxHeight: "calc(100% - 80px)" }}>
                        {props && props.length > 0 ? (
                            props.map((prop) => {
                                const hitRate = calculateHitRate(player.stats, prop.prop_type, prop.line);
                                const isGoodBet = hitRate > 55;

                                return (
                                    <div key={prop.id} className="bg-white/5 rounded-lg p-2">
                                        <div className="flex items-center justify-between mb-1.5">
                                            <span className="text-[10px] text-muted uppercase">{prop.prop_type.replace('+', ' + ')}</span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-base font-bold text-white">{prop.line}</span>
                                                {isGoodBet && (
                                                    <span className="text-[8px] bg-emerald-500/20 text-emerald-400 px-1 py-0.5 rounded">
                                                        {hitRate.toFixed(0)}% hit
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-2 gap-1.5">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onTogglePick(`${player.id}-${prop.id}`, 'over'); }}
                                                className={`rounded py-1.5 text-center transition-colors ${
                                                    selectedPicks[`${player.id}-${prop.id}`] === 'over'
                                                        ? 'bg-emerald-500/40 border-2 border-emerald-400'
                                                        : hitRate > 50
                                                            ? 'bg-emerald-500/20 border border-emerald-500/30'
                                                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                }`}
                                            >
                                                <div className="text-[9px] text-muted">Over</div>
                                                <div className={`text-xs font-bold ${selectedPicks[`${player.id}-${prop.id}`] === 'over' || hitRate > 50 ? 'text-emerald-400' : 'text-white'}`}>{formatOdds(prop.over_odds)}</div>
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); onTogglePick(`${player.id}-${prop.id}`, 'under'); }}
                                                className={`rounded py-1.5 text-center transition-colors ${
                                                    selectedPicks[`${player.id}-${prop.id}`] === 'under'
                                                        ? 'bg-red-500/40 border-2 border-red-400'
                                                        : hitRate <= 50
                                                            ? 'bg-red-500/20 border border-red-500/30'
                                                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                                }`}
                                            >
                                                <div className="text-[9px] text-muted">Under</div>
                                                <div className={`text-xs font-bold ${selectedPicks[`${player.id}-${prop.id}`] === 'under' || hitRate <= 50 ? 'text-red-400' : 'text-white'}`}>{formatOdds(prop.under_odds)}</div>
                                            </button>
                                        </div>
                                    </div>
                                );
                            })
                        ) : (
                            <div className="text-center text-muted py-4 text-xs">
                                Loading props...
                            </div>
                        )}
                    </div>

                    {/* Footer - Fixed */}
                    <div className="p-2 border-t border-white/10 text-center flex-shrink-0">
                        <div className="inline-flex items-center gap-1 text-[10px] text-muted/50">
                            <RotateCw size={10} />
                            <span>Tap to flip back</span>
                        </div>
                    </div>
                </div>
            </motion.div>
        </motion.div>
    );
};

export const Players: React.FC = () => {
    const [search, setSearch] = useState("");
    const [selectedPicks, setSelectedPicks] = useState<Record<string, 'over' | 'under'>>({});
    const { data: players, isLoading } = useQuery({
        queryKey: ["players"],
        queryFn: fetchPlayers
    });

    const togglePick = (key: string, side: 'over' | 'under') => {
        setSelectedPicks(prev => {
            if (prev[key] === side) {
                const { [key]: _, ...rest } = prev;
                return rest;
            }
            return { ...prev, [key]: side };
        });
    };

    const filtered = players?.filter(p =>
        p.name.toLowerCase().includes(search.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        <Users size={24} />
                    </div>
                    <h1 className="text-2xl font-bold text-white">Player Directory</h1>
                    <span className="text-xs text-muted bg-white/5 px-2 py-1 rounded-full">
                        {players?.length || 0} players
                    </span>
                </div>

                <div className="relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                    <input
                        type="text"
                        placeholder="Search players..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-muted outline-none focus:border-primary w-64"
                    />
                </div>
            </div>

            {isLoading ? (
                <div className="flex justify-center p-10">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {filtered?.map((player, i) => (
                        <PlayerFlipCard key={player.id} player={player} index={i} selectedPicks={selectedPicks} onTogglePick={togglePick} />
                    ))}
                </div>
            )}

            {filtered?.length === 0 && !isLoading && (
                <div className="text-center text-muted py-10">
                    No players found matching "{search}"
                </div>
            )}
        </div>
    );
};
