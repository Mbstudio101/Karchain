import React, { useState, useMemo, useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAdvancedProps } from "../api";
import { Search, Filter, Target, ArrowUpDown, ChevronDown, Star, Zap, TrendingUp, TrendingDown, Shield } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAvailableDates } from "../hooks/useAvailableDates";
import { getLocalISODate } from "../lib/utils";

const PROP_TYPES = [
    'all',
    'points',
    'rebounds',
    'assists',
    'steals',
    'blocks',
    'pts+reb+ast',
];

const SORT_OPTIONS = [
    { value: 'ev', label: 'Best EV' },
    { value: 'edge', label: 'Best Edge' },
    { value: 'hitRate', label: 'Hit Rate' },
    { value: 'grade', label: 'Grade' },
    { value: 'player', label: 'Player Name' },
];

const GRADE_ORDER: Record<string, number> = { 'S': 0, 'A+': 1, 'A': 2, 'B+': 3, 'B': 4 };

const gradeColor = (grade: string) => {
    if (grade === 'S') return 'text-yellow-300 bg-yellow-500/20 border-yellow-500/40';
    if (grade === 'A+') return 'text-emerald-300 bg-emerald-500/20 border-emerald-500/40';
    if (grade === 'A') return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
    if (grade === 'B+') return 'text-blue-400 bg-blue-500/10 border-blue-500/30';
    return 'text-gray-400 bg-white/5 border-white/10';
};

const streakBadge = (streak: string) => {
    if (streak === 'hot') return <span className="text-[9px] bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded font-bold flex items-center gap-0.5"><TrendingUp size={9} /> HOT</span>;
    if (streak === 'cold') return <span className="text-[9px] bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-bold flex items-center gap-0.5"><TrendingDown size={9} /> COLD</span>;
    return null;
};

const formatOdds = (odds: number) => (odds > 0 ? `+${odds}` : `${odds}`);

export const PropsFinder: React.FC = () => {
    const [search, setSearch] = useState("");
    const [propTypeFilter, setPropTypeFilter] = useState("all");
    const [sortBy, setSortBy] = useState("ev");
    const [minEdge, setMinEdge] = useState(0);
    const [showFilters, setShowFilters] = useState(true);
    const [selectedPicks, setSelectedPicks] = useState<Record<number, 'over' | 'under'>>({});
    const { availableDates, defaultDate } = useAvailableDates();
    const [selectedDate, setSelectedDate] = useState(() => {
        // Use the next available date if available, otherwise today
        return defaultDate || getLocalISODate();
    });
    const [overUnderFilter, setOverUnderFilter] = useState<string>("");
    const [copyStatus, setCopyStatus] = useState("");

    // Update selected date when default date is available
    useEffect(() => {
        if (defaultDate) {
            setSelectedDate(defaultDate);
        }
    }, [defaultDate]);

    const displayedDates = useMemo(() => (
        availableDates.includes(selectedDate) ? availableDates : [selectedDate, ...availableDates]
    ), [availableDates, selectedDate]);

    const togglePick = (propId: number, side: 'over' | 'under') => {
        setSelectedPicks(prev => {
            if (prev[propId] === side) {
                const { [propId]: _, ...rest } = prev;
                return rest;
            }
            return { ...prev, [propId]: side };
        });
    };

    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["advancedProps", selectedDate, overUnderFilter],
        queryFn: () => fetchAdvancedProps(0, 0, selectedDate, overUnderFilter),
        // Removed polling in favor of WebSocket updates
    });

    useEffect(() => {
        if (data?.date_used && data.date_used !== selectedDate) {
            setSelectedDate(data.date_used);
        }
    }, [data?.date_used, selectedDate]);

    // Listen for WebSocket updates
    useEffect(() => {
        const handlePropsUpdate = () => {
            queryClient.invalidateQueries({ queryKey: ["advancedProps"] });
        };

        window.addEventListener("propsUpdated", handlePropsUpdate);
        return () => window.removeEventListener("propsUpdated", handlePropsUpdate);
    }, [queryClient]);

    const props = data?.props || [];
    const propsById = useMemo(() => {
        return new Map(props.map((p) => [p.prop_id, p]));
    }, [props]);

    // Filter and sort
    const filteredProps = useMemo(() => {
        let result = [...props];

        if (search) {
            result = result.filter(p =>
                p.player_name.toLowerCase().includes(search.toLowerCase())
            );
        }

        if (propTypeFilter !== 'all') {
            result = result.filter(p => p.prop_type === propTypeFilter);
        }

        if (minEdge > 0) {
            result = result.filter(p => p.edge >= minEdge);
        }

        result.sort((a, b) => {
            switch (sortBy) {
                case 'ev': return b.ev - a.ev;
                case 'edge': return b.edge - a.edge;
                case 'hitRate': return b.hit_rate - a.hit_rate;
                case 'grade': return (GRADE_ORDER[a.grade] ?? 99) - (GRADE_ORDER[b.grade] ?? 99);
                case 'player': return a.player_name.localeCompare(b.player_name);
                default: return 0;
            }
        });

        return result;
    }, [props, search, propTypeFilter, minEdge, sortBy]);

    // Stats summary
    const summary = useMemo(() => {
        const valueBets = props.filter(p => p.edge >= 5);
        const avgEv = valueBets.length ? valueBets.reduce((a, p) => a + p.ev, 0) / valueBets.length : 0;
        const sGrade = props.filter(p => p.grade === 'S').length;
        return { total: props.length, valueBets: valueBets.length, avgEv, sGrade };
    }, [props]);

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
                        <p className="text-xs text-muted">AI-powered player prop analysis with opponent adjustments</p>
                    </div>
                </div>

                {/* Stats Summary */}
                <div className="flex gap-3">
                    <div className="bg-white/5 rounded-lg px-4 py-2 text-center">
                        <div className="text-lg font-bold text-white">{summary.total}</div>
                        <div className="text-[10px] text-muted uppercase">Total Props</div>
                    </div>
                    <div className="bg-emerald-500/10 rounded-lg px-4 py-2 text-center border border-emerald-500/20">
                        <div className="text-lg font-bold text-emerald-400">{summary.valueBets}</div>
                        <div className="text-[10px] text-emerald-400/70 uppercase">Value Bets</div>
                    </div>
                    {summary.sGrade > 0 && (
                        <div className="bg-yellow-500/10 rounded-lg px-4 py-2 text-center border border-yellow-500/20">
                            <div className="text-lg font-bold text-yellow-300">{summary.sGrade}</div>
                            <div className="text-[10px] text-yellow-400/70 uppercase">S-Grade</div>
                        </div>
                    )}
                    <div className="bg-purple-500/10 rounded-lg px-4 py-2 text-center border border-purple-500/20">
                        <div className="text-lg font-bold text-purple-400">${summary.avgEv.toFixed(1)}</div>
                        <div className="text-[10px] text-purple-400/70 uppercase">Avg EV</div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="bg-card border border-white/10 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 text-sm text-muted">
                        <Filter size={14} />
                        <span>Filters</span>
                        {(overUnderFilter || search || propTypeFilter !== 'all' || minEdge > 0) && (
                            <span className="text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                                Active
                            </span>
                        )}
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
                            className="grid grid-cols-1 md:grid-cols-5 gap-4"
                        >
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

                            <div className="relative">
                                <select
                                    value={selectedDate}
                                    onChange={e => setSelectedDate(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-primary appearance-none"
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

                            <div className="relative">
                                <select
                                    value={overUnderFilter}
                                    onChange={e => setOverUnderFilter(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-primary appearance-none"
                                >
                                    <option value="" className="bg-card">All Picks</option>
                                    <option value="over" className="bg-card">Over Only</option>
                                    <option value="under" className="bg-card">Under Only</option>
                                </select>
                                <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
                            </div>

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
                    {filteredProps.slice(0, 500).map((prop, i) => {
                        const isValueBet = prop.edge >= 5;

                        return (
                            <motion.div
                                key={prop.prop_id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.02 }}
                                className={`bg-card border rounded-xl p-4 ${isValueBet ? 'border-emerald-500/40' : 'border-white/10'}`}
                            >
                                {/* Header */}
                                <div className="flex items-start gap-3 mb-3">
                                    {prop.team_logo && (
                                        <img src={prop.team_logo} alt={prop.team_name} className="w-8 h-8 object-contain" />
                                    )}
                                    <div className="flex-1 min-w-0">
                                        <div className="font-bold text-white text-sm leading-tight">{prop.player_name}</div>
                                        <div className="text-[10px] text-muted flex items-center gap-1">
                                            {prop.player_position}
                                            {prop.team_name && <span>• {prop.team_name}</span>}
                                            {prop.opponent && <span>vs {prop.opponent}</span>}
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-1.5 shrink-0">
                                        {streakBadge(prop.streak_status)}
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded border ${gradeColor(prop.grade)}`}>
                                            {prop.grade}
                                        </span>
                                    </div>
                                </div>

                                {/* Prop Details */}
                                <div className="bg-white/5 rounded-lg p-3 mb-3">
                                    <div className="flex items-center justify-between mb-2">
                                        <span className="text-xs text-muted uppercase">{prop.prop_type.replace('+', ' + ')}</span>
                                        <span className="text-lg font-bold text-white">{prop.line}</span>
                                    </div>
                                    <div className="flex items-center justify-between text-[10px]">
                                        <div className="text-muted">
                                            Proj: <span className="text-white font-bold">{prop.weighted_avg.toFixed(1)}</span>
                                            {' '} Hit: <span className={`font-bold ${prop.hit_rate > 55 ? 'text-emerald-400' : prop.hit_rate < 45 ? 'text-red-400' : 'text-white'}`}>
                                                {prop.hit_rate.toFixed(0)}%
                                            </span>
                                        </div>
                                        <div className="text-muted">
                                            CI: {prop.confidence_interval.low.toFixed(0)}-{prop.confidence_interval.high.toFixed(0)}%
                                        </div>
                                    </div>

                                    {/* Signal badges */}
                                    <div className="flex flex-wrap gap-1 mt-2">
                                        {prop.opponent_adjusted && (
                                            <span className="text-[8px] bg-blue-500/15 text-blue-400 px-1 py-0.5 rounded flex items-center gap-0.5">
                                                <Shield size={7} /> OPP ADJ
                                            </span>
                                        )}
                                        {prop.bp_star_rating && (
                                            <span className="text-[8px] bg-amber-500/15 text-amber-400 px-1 py-0.5 rounded flex items-center gap-0.5">
                                                <Star size={7} /> BP {prop.bp_star_rating.toFixed(1)}
                                            </span>
                                        )}
                                        {prop.bp_agrees && prop.bp_star_rating && (
                                            <span className="text-[8px] bg-emerald-500/15 text-emerald-400 px-1 py-0.5 rounded">BP AGREES</span>
                                        )}
                                        {prop.is_b2b && (
                                            <span className="text-[8px] bg-red-500/15 text-red-400 px-1 py-0.5 rounded">B2B</span>
                                        )}
                                    </div>
                                </div>

                                {/* EV / Edge / Kelly row */}
                                <div className="grid grid-cols-3 gap-2 mb-3 text-center">
                                    <div>
                                        <div className="text-[9px] text-muted">EV</div>
                                        <div className={`text-xs font-bold ${prop.ev > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                                            {prop.ev > 0 ? '+' : ''}${prop.ev.toFixed(2)}
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-[9px] text-muted">Edge</div>
                                        <div className={`text-xs font-bold ${prop.edge > 5 ? 'text-emerald-400' : prop.edge > 0 ? 'text-white' : 'text-red-400'}`}>
                                            {prop.edge > 0 ? '+' : ''}{prop.edge.toFixed(1)}%
                                        </div>
                                    </div>
                                    <div>
                                        <div className="text-[9px] text-muted">Kelly</div>
                                        <div className="text-xs font-bold text-purple-400">{prop.kelly_bet_size}</div>
                                    </div>
                                </div>

                                {/* Over/Under Buttons */}
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        onClick={() => togglePick(prop.prop_id, 'over')}
                                        className={`rounded-lg py-2 text-center transition-colors ${
                                            selectedPicks[prop.prop_id] === 'over'
                                                ? 'bg-emerald-500/40 border-2 border-emerald-400 ring-1 ring-emerald-400/50'
                                                : prop.recommendation === 'over'
                                                    ? 'bg-emerald-500/30 border border-emerald-500/50'
                                                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                        }`}
                                    >
                                        <div className="text-[9px] text-muted">Over</div>
                                        <div className={`text-sm font-bold ${selectedPicks[prop.prop_id] === 'over' || prop.recommendation === 'over' ? 'text-emerald-400' : 'text-white'}`}>
                                            {formatOdds(prop.over_odds)}
                                        </div>
                                        {prop.recommendation === 'over' && (
                                            <div className="text-[8px] text-emerald-400 flex items-center justify-center gap-0.5 mt-0.5">
                                                <Zap size={8} /> REC
                                            </div>
                                        )}
                                    </button>
                                    <button
                                        onClick={() => togglePick(prop.prop_id, 'under')}
                                        className={`rounded-lg py-2 text-center transition-colors ${
                                            selectedPicks[prop.prop_id] === 'under'
                                                ? 'bg-red-500/40 border-2 border-red-400 ring-1 ring-red-400/50'
                                                : prop.recommendation === 'under'
                                                    ? 'bg-red-500/30 border border-red-500/50'
                                                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                        }`}
                                    >
                                        <div className="text-[9px] text-muted">Under</div>
                                        <div className={`text-sm font-bold ${selectedPicks[prop.prop_id] === 'under' || prop.recommendation === 'under' ? 'text-red-400' : 'text-white'}`}>
                                            {formatOdds(prop.under_odds)}
                                        </div>
                                        {prop.recommendation === 'under' && (
                                            <div className="text-[8px] text-red-400 flex items-center justify-center gap-0.5 mt-0.5">
                                                <Zap size={8} /> REC
                                            </div>
                                        )}
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            )}

            {filteredProps.length === 0 && !isLoading && (
                <div className="text-center text-muted py-10">
                    No props found for {new Date(selectedDate).toLocaleDateString('en-US', { 
                        month: 'long', 
                        day: 'numeric',
                        year: 'numeric'
                    })}
                    <br />
                    <span className="text-xs opacity-50">Try adjusting filters or select a different date</span>
                </div>
            )}

            {filteredProps.length > 500 && (
                <div className="text-center text-muted text-sm">
                    Showing 500 of {filteredProps.length} props. Refine your filters to see more.
                </div>
            )}

            {/* Selected Picks Summary Bar */}
            <AnimatePresence>
                                    {Object.keys(selectedPicks).length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-card border border-primary/40 rounded-2xl px-6 py-3 shadow-2xl shadow-black/50 flex items-center gap-4 z-50"
                    >
                        <div className="text-sm text-white">
                            <span className="font-bold text-primary">{Object.keys(selectedPicks).length}</span> pick{Object.keys(selectedPicks).length !== 1 ? 's' : ''} selected
                        </div>
                        {copyStatus && <div className="text-xs text-emerald-300">{copyStatus}</div>}
                        <button
                            onClick={async () => {
                                const lines = Object.entries(selectedPicks).map(([propId, side]) => {
                                    const prop = propsById.get(Number(propId));
                                    if (!prop) return `${propId}: ${side.toUpperCase()}`;
                                    const odds = side === "over" ? prop.over_odds : prop.under_odds;
                                    const oddsText = odds > 0 ? `+${odds}` : `${odds}`;
                                    return `${prop.player_name} ${prop.prop_type} ${side.toUpperCase()} ${prop.line} (${oddsText})`;
                                });
                                await navigator.clipboard.writeText(lines.join("\n"));
                                setCopyStatus("Copied");
                                window.setTimeout(() => setCopyStatus(""), 1500);
                            }}
                            className="text-xs text-primary hover:text-emerald-300 transition-colors"
                        >
                            Copy Picks
                        </button>
                        <button
                            onClick={() => setSelectedPicks({})}
                            className="text-xs text-muted hover:text-white transition-colors"
                        >
                            Clear All
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
