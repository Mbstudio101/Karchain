import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api";
import { BarChart3, TrendingUp, PieChart, Target, DollarSign, Percent } from "lucide-react";
import { ResponsiveContainer, PieChart as RechartsPie, Cell, Pie, Tooltip } from "recharts";
import { motion } from "framer-motion";

interface AnalyticsData {
    totalProps: number;
    valueBets: number;
    avgEdge: number;
    totalPlayers: number;
    totalGames: number;
    propsBreakdown: { type: string; count: number }[];
}

const fetchAnalytics = async (): Promise<AnalyticsData> => {
    const [props, players, games] = await Promise.all([
        api.get("/players/props/all?limit=1000"),
        api.get("/players/"),
        api.get("/games/")
    ]);

    const propsData = props.data || [];
    const playersData = players.data || [];
    const gamesData = games.data || [];

    // Calculate props breakdown
    const propTypeCounts: Record<string, number> = {};
    propsData.forEach((p: any) => {
        propTypeCounts[p.prop_type] = (propTypeCounts[p.prop_type] || 0) + 1;
    });

    // Calculate real value bets and average edge from props odds
    let valueBetsCount = 0;
    let totalEdge = 0;
    let validPropsCount = 0;

    propsData.forEach((p: any) => {
        // Calculate implied probability and edge for over/under
        if (p.over_odds && p.over_odds !== 0) {
            const impliedProb = p.over_odds > 0
                ? 100 / (p.over_odds + 100)
                : Math.abs(p.over_odds) / (Math.abs(p.over_odds) + 100);
            // Assume 50% true probability, calculate edge
            const edge = (0.5 - impliedProb) * 100;
            if (edge > 3) {
                valueBetsCount++;
                totalEdge += edge;
                validPropsCount++;
            }
        }
        if (p.under_odds && p.under_odds !== 0) {
            const impliedProb = p.under_odds > 0
                ? 100 / (p.under_odds + 100)
                : Math.abs(p.under_odds) / (Math.abs(p.under_odds) + 100);
            const edge = (0.5 - impliedProb) * 100;
            if (edge > 3) {
                valueBetsCount++;
                totalEdge += edge;
                validPropsCount++;
            }
        }
    });

    const avgEdge = validPropsCount > 0 ? totalEdge / validPropsCount : 0;

    return {
        totalProps: propsData.length,
        valueBets: valueBetsCount,
        avgEdge: parseFloat(avgEdge.toFixed(1)),
        totalPlayers: playersData.length,
        totalGames: gamesData.length,
        propsBreakdown: Object.entries(propTypeCounts).map(([type, count]) => ({ type, count }))
    };
};

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'];

export const Analysis: React.FC = () => {
    const { data: analytics, isLoading } = useQuery({
        queryKey: ["analytics"],
        queryFn: fetchAnalytics,
        staleTime: 1000 * 60 * 5
    });

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                    <BarChart3 size={24} />
                </div>
                <h1 className="text-2xl font-bold text-white">Market Analytics</h1>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="bg-card border border-white/10 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 text-muted text-xs mb-2">
                        <Target size={14} />
                        <span>Total Props</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{analytics?.totalProps || 0}</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 }}
                    className="bg-gradient-to-br from-emerald-500/10 to-emerald-900/10 border border-emerald-500/20 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 text-emerald-400 text-xs mb-2">
                        <DollarSign size={14} />
                        <span>Value Bets</span>
                    </div>
                    <div className="text-2xl font-bold text-emerald-400">{analytics?.valueBets || 0}</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="bg-card border border-white/10 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 text-muted text-xs mb-2">
                        <Percent size={14} />
                        <span>Avg Edge</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{analytics?.avgEdge?.toFixed(1) || 0}%</div>
                </motion.div>

                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="bg-card border border-white/10 rounded-xl p-4"
                >
                    <div className="flex items-center gap-2 text-muted text-xs mb-2">
                        <TrendingUp size={14} />
                        <span>Live Games</span>
                    </div>
                    <div className="text-2xl font-bold text-white">{analytics?.totalGames || 0}</div>
                </motion.div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Props Distribution Chart */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-card border border-white/5 rounded-2xl p-6"
                >
                    <div className="flex items-center gap-2 mb-6">
                        <PieChart size={18} className="text-blue-500" />
                        <h3 className="font-bold text-white">Props by Type</h3>
                    </div>

                    <div className="h-[250px] min-h-[200px] flex items-center justify-center">
                        {analytics?.propsBreakdown && analytics.propsBreakdown.length > 0 ? (
                            <ResponsiveContainer width="100%" height={250} minHeight={200}>
                                <RechartsPie>
                                    <Pie
                                        data={analytics.propsBreakdown}
                                        dataKey="count"
                                        nameKey="type"
                                        cx="50%"
                                        cy="50%"
                                        outerRadius={80}
                                        label
                                    >
                                        {analytics.propsBreakdown.map((_, i) => (
                                            <Cell key={i} fill={COLORS[i % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </RechartsPie>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-muted text-sm">No props data available</div>
                        )}
                    </div>
                </motion.div>

                {/* Players & Stats Overview */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.1 }}
                    className="bg-card border border-white/5 rounded-2xl p-6 relative overflow-hidden"
                >
                    <div className="flex items-center gap-2 mb-6">
                        <TrendingUp size={18} className="text-emerald-500" />
                        <h3 className="font-bold text-white">Coverage Summary</h3>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                            <span className="text-muted text-sm">Players Tracked</span>
                            <span className="text-white font-bold">{analytics?.totalPlayers || 0}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                            <span className="text-muted text-sm">Props Available</span>
                            <span className="text-white font-bold">{analytics?.totalProps || 0}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                            <span className="text-muted text-sm">Games Today</span>
                            <span className="text-white font-bold">{analytics?.totalGames || 0}</span>
                        </div>
                        <div className="flex items-center justify-between p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                            <span className="text-emerald-400 text-sm">Value Bets Found</span>
                            <span className="text-emerald-400 font-bold">{analytics?.valueBets || 0}</span>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};
