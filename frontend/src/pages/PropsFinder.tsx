import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { Search, Filter, Target, ArrowUpDown, ChevronDown } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface PlayerStats {
    points: number;
    rebounds: number;
    assists: number;
    steals?: number;
    blocks?: number;
}

interface PlayerProp {
    id: number;
    player_id: number;
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
    headshot_url: string | null;
    stats: PlayerStats[];
}

interface EnrichedProp extends PlayerProp {
    player: Player;
    hitRate: number;
    overEdge: number;
    underEdge: number;
    recommendation: 'over' | 'under' | null;
    avgValue: number;
}

const PROP_TYPES = ['all', 'points', 'rebounds', 'assists', 'pts+reb+ast'];
const SORT_OPTIONS = [
    { value: 'edge', label: 'Best Edge' },
    { value: 'hitRate', label: 'Hit Rate' },
    { value: 'line', label: 'Line' },
    { value: 'player', label: 'Player Name' },
];

const fetchPlayers = async () => {
    const { data } = await api.get<Player[]>("/players/");
    return data;
};

const fetchAllProps = async () => {
    const { data } = await api.get<PlayerProp[]>("/players/props/all?limit=500");
    return data;
};

// Calculate hit rate for a prop
const calculateHitRate = (stats: PlayerStats[], propType: string, line: number): number => {
    if (!stats.length) return 0;

    let hits = 0;
    for (const stat of stats) {
        let value = 0;
        if (propType === 'points') value = stat.points || 0;
        else if (propType === 'rebounds') value = stat.rebounds || 0;
        else if (propType === 'assists') value = stat.assists || 0;
        else if (propType === 'pts+reb+ast') value = (stat.points || 0) + (stat.rebounds || 0) + (stat.assists || 0);

        if (value > line) hits++;
    }
    return (hits / stats.length) * 100;
};

// Calculate edge based on odds and probability
const calculateEdge = (odds: number, probability: number): number => {
    const prob = probability / 100;
    let decimal: number;
    if (odds > 0) {
        decimal = 1 + (odds / 100);
    } else {
        decimal = 1 + (100 / Math.abs(odds));
    }
    const implied = (1 / decimal) * 100;
    return prob * 100 - implied;
};

const formatOdds = (odds: number) => (odds > 0 ? `+${odds}` : `${odds}`);

export const PropsFinder: React.FC = () => {
    const [search, setSearch] = useState("");
    const [propTypeFilter, setPropTypeFilter] = useState("all");
    const [sortBy, setSortBy] = useState("edge");
    const [minEdge, setMinEdge] = useState(0);
    const [showFilters, setShowFilters] = useState(true);

    const { data: players } = useQuery({
        queryKey: ["players"],
        queryFn: fetchPlayers
    });

    const { data: props, isLoading } = useQuery({
        queryKey: ["allProps"],
        queryFn: fetchAllProps
    });

    // Enrich props with player data and analytics
    const enrichedProps = useMemo(() => {
        if (!props || !players) return [];

        const playerMap = new Map(players.map(p => [p.id, p]));

        return props.map(prop => {
            const player = playerMap.get(prop.player_id);
            if (!player || !player.stats.length) return null;

            const hitRate = calculateHitRate(player.stats, prop.prop_type, prop.line);
            const overEdge = calculateEdge(prop.over_odds, hitRate);
            const underEdge = calculateEdge(prop.under_odds, 100 - hitRate);

            let avgValue = 0;
            if (prop.prop_type === 'points') avgValue = player.stats.reduce((a, s) => a + (s.points || 0), 0) / player.stats.length;
            else if (prop.prop_type === 'rebounds') avgValue = player.stats.reduce((a, s) => a + (s.rebounds || 0), 0) / player.stats.length;
            else if (prop.prop_type === 'assists') avgValue = player.stats.reduce((a, s) => a + (s.assists || 0), 0) / player.stats.length;
            else if (prop.prop_type === 'pts+reb+ast') avgValue = player.stats.reduce((a, s) => a + (s.points || 0) + (s.rebounds || 0) + (s.assists || 0), 0) / player.stats.length;

            const recommendation = overEdge > underEdge && overEdge > 3 ? 'over' : underEdge > overEdge && underEdge > 3 ? 'under' : null;

            return {
                ...prop,
                player,
                hitRate,
                overEdge,
                underEdge,
                recommendation,
                avgValue
            } as EnrichedProp;
        }).filter((p): p is EnrichedProp => p !== null);
    }, [props, players]);

    // Filter and sort
    const filteredProps = useMemo(() => {
        let result = enrichedProps;

        // Search filter
        if (search) {
            result = result.filter(p =>
                p.player.name.toLowerCase().includes(search.toLowerCase())
            );
        }

        // Prop type filter
        if (propTypeFilter !== 'all') {
            result = result.filter(p => p.prop_type === propTypeFilter);
        }

        // Min edge filter
        if (minEdge > 0) {
            result = result.filter(p => Math.max(p.overEdge, p.underEdge) >= minEdge);
        }

        // Sort
        result = [...result].sort((a, b) => {
            switch (sortBy) {
                case 'edge':
                    return Math.max(b.overEdge, b.underEdge) - Math.max(a.overEdge, a.underEdge);
                case 'hitRate':
                    return b.hitRate - a.hitRate;
                case 'line':
                    return b.line - a.line;
                case 'player':
                    return a.player.name.localeCompare(b.player.name);
                default:
                    return 0;
            }
        });

        return result;
    }, [enrichedProps, search, propTypeFilter, minEdge, sortBy]);

    // Stats summary
    const summary = useMemo(() => {
        const valueBets = enrichedProps.filter(p => Math.max(p.overEdge, p.underEdge) >= 5);
        const avgEdge = valueBets.length ? valueBets.reduce((a, p) => a + Math.max(p.overEdge, p.underEdge), 0) / valueBets.length : 0;
        return { total: enrichedProps.length, valueBets: valueBets.length, avgEdge };
    }, [enrichedProps]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                        <Target size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Props Finder</h1>
                        <p className="text-xs text-muted">Find the best value player props</p>
                    </div>
                </div>

                {/* Stats Summary */}
                <div className="flex gap-4">
                    <div className="bg-white/5 rounded-lg px-4 py-2 text-center">
                        <div className="text-lg font-bold text-white">{summary.total}</div>
                        <div className="text-[10px] text-muted uppercase">Total Props</div>
                    </div>
                    <div className="bg-emerald-500/10 rounded-lg px-4 py-2 text-center border border-emerald-500/20">
                        <div className="text-lg font-bold text-emerald-400">{summary.valueBets}</div>
                        <div className="text-[10px] text-emerald-400/70 uppercase">Value Bets</div>
                    </div>
                    <div className="bg-purple-500/10 rounded-lg px-4 py-2 text-center border border-purple-500/20">
                        <div className="text-lg font-bold text-purple-400">{summary.avgEdge.toFixed(1)}%</div>
                        <div className="text-[10px] text-purple-400/70 uppercase">Avg Edge</div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-card border border-white/10 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-sm text-muted">
                        <Filter size={14} />
                        <span>Filters</span>
                    </div>
                    <button
                        onClick={() => setShowFilters(!showFilters)}
                        className="text-xs text-muted hover:text-white"
                    >
                        {showFilters ? 'Hide' : 'Show'}
                    </button>
                </div>

                <AnimatePresence>
                    {showFilters && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="grid grid-cols-1 md:grid-cols-4 gap-4"
                        >
                            {/* Search */}
                            <div className="relative">
                                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                                <input
                                    type="text"
                                    placeholder="Search player..."
                                    value={search}
                                    onChange={e => setSearch(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-muted outline-none focus:border-primary"
                                />
                            </div>

                            {/* Prop Type */}
                            <div className="relative">
                                <select
                                    value={propTypeFilter}
                                    onChange={e => setPropTypeFilter(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-primary appearance-none"
                                >
                                    {PROP_TYPES.map(type => (
                                        <option key={type} value={type} className="bg-card">
                                            {type === 'all' ? 'All Props' : type.toUpperCase()}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
                            </div>

                            {/* Min Edge */}
                            <div className="relative">
                                <input
                                    type="range"
                                    min="0"
                                    max="20"
                                    value={minEdge}
                                    onChange={e => setMinEdge(Number(e.target.value))}
                                    className="w-full"
                                />
                                <div className="text-xs text-muted mt-1">Min Edge: {minEdge}%+</div>
                            </div>

                            {/* Sort */}
                            <div className="relative">
                                <ArrowUpDown size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
                                <select
                                    value={sortBy}
                                    onChange={e => setSortBy(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-2 text-sm text-white outline-none focus:border-primary appearance-none"
                                >
                                    {SORT_OPTIONS.map(opt => (
                                        <option key={opt.value} value={opt.value} className="bg-card">
                                            {opt.label}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Props List */}
            {isLoading ? (
                <div className="flex justify-center p-10">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredProps.slice(0, 50).map((prop, i) => {
                        const bestEdge = Math.max(prop.overEdge, prop.underEdge);
                        const isValueBet = bestEdge >= 5;

                        return (
                            <motion.div
                                key={prop.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.02 }}
                                className={`bg-card border rounded-xl p-4 ${isValueBet ? 'border-emerald-500/40' : 'border-white/10'}`}
                            >
                                {/* Header */}
                                <div className="flex items-start gap-3 mb-3">
                                    <div className="w-10 h-10 rounded-full bg-white/5 overflow-hidden flex-shrink-0">
                                        {prop.player.headshot_url ? (
                                            <img src={prop.player.headshot_url} alt={prop.player.name} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-sm font-bold text-muted">
                                                {prop.player.name.charAt(0)}
                                            </div>
                                        )}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-bold text-white text-sm leading-tight" title={prop.player.name}>{prop.player.name}</div>
                                        <div className="text-[10px] text-muted">{prop.player.position} • {prop.player.sport}</div>
                                    </div>
                                    {isValueBet && (
                                        <span className="text-[9px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded font-bold">
                                            VALUE
                                        </span>
                                    )}
                                </div>

                                {/* Prop Details */}
                                <div className="bg-white/5 rounded-lg p-3 mb-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-muted uppercase">{prop.prop_type.replace('+', ' + ')}</span>
                                        <span className="text-lg font-bold text-white">{prop.line}</span>
                                    </div>
                                    <div className="text-[10px] text-muted">
                                        Avg: <span className="text-white font-bold">{prop.avgValue.toFixed(1)}</span> •
                                        Hit Rate: <span className={`font-bold ${prop.hitRate > 55 ? 'text-emerald-400' : prop.hitRate < 45 ? 'text-red-400' : 'text-white'}`}>
                                            {prop.hitRate.toFixed(0)}%
                                        </span>
                                    </div>
                                </div>

                                {/* Over/Under Buttons */}
                                <div className="grid grid-cols-2 gap-2">
                                    <button className={`rounded-lg py-2 text-center transition-colors ${prop.recommendation === 'over' ? 'bg-emerald-500/30 border border-emerald-500/50' : 'bg-white/5 border border-white/10 hover:bg-white/10'}`}>
                                        <div className="text-[9px] text-muted">Over</div>
                                        <div className={`text-sm font-bold ${prop.recommendation === 'over' ? 'text-emerald-400' : 'text-white'}`}>
                                            {formatOdds(prop.over_odds)}
                                        </div>
                                        <div className={`text-[9px] ${prop.overEdge > 3 ? 'text-emerald-400' : 'text-muted'}`}>
                                            {prop.overEdge > 0 ? '+' : ''}{prop.overEdge.toFixed(1)}% edge
                                        </div>
                                    </button>
                                    <button className={`rounded-lg py-2 text-center transition-colors ${prop.recommendation === 'under' ? 'bg-red-500/30 border border-red-500/50' : 'bg-white/5 border border-white/10 hover:bg-white/10'}`}>
                                        <div className="text-[9px] text-muted">Under</div>
                                        <div className={`text-sm font-bold ${prop.recommendation === 'under' ? 'text-red-400' : 'text-white'}`}>
                                            {formatOdds(prop.under_odds)}
                                        </div>
                                        <div className={`text-[9px] ${prop.underEdge > 3 ? 'text-red-400' : 'text-muted'}`}>
                                            {prop.underEdge > 0 ? '+' : ''}{prop.underEdge.toFixed(1)}% edge
                                        </div>
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            )}

            {filteredProps.length === 0 && !isLoading && (
                <div className="text-center text-muted py-10">
                    No props found matching your filters
                </div>
            )}

            {filteredProps.length > 50 && (
                <div className="text-center text-muted text-sm">
                    Showing 50 of {filteredProps.length} props. Refine your filters to see more.
                </div>
            )}
        </div>
    );
};
