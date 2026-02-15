import React, { useEffect, useState } from "react";
import { useGames } from "../hooks/useGames";
import { GameCard } from "../components/dashboard/GameCard";
import { RecommendationFeed } from "../components/dashboard/RecommendationFeed";
import { useAvailableDates } from "../hooks/useAvailableDates";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
import { getLocalISODate } from "../lib/utils";

export const Dashboard: React.FC = () => {
    const { availableDates, defaultDate } = useAvailableDates();
    const systemDate = getLocalISODate();
    const [selectedDate, setSelectedDate] = useState(systemDate);
    useEffect(() => {
        if (defaultDate) {
            setSelectedDate(defaultDate);
        }
    }, [defaultDate]);
    const displayedDates = availableDates.includes(selectedDate)
        ? availableDates
        : [selectedDate, ...availableDates];

    const shiftSelectedDate = (deltaDays: number) => {
        const d = new Date(selectedDate);
        d.setDate(d.getDate() + deltaDays);
        setSelectedDate(getLocalISODate(d));
    };

    const { data: games, isLoading, isError } = useGames(selectedDate);

    if (isLoading) return (
        <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
    );

    if (isError) return <div className="text-red-500">Failed to load games. Is the backend running?</div>;

    return (
        <div className="flex flex-col gap-8">
            {/* Top Row: Recommendations */}
            <div className="grid grid-cols-1 gap-6">
                <RecommendationFeed />
            </div>

            {/* Games Grid */}
            <div>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        Live Markets
                        <span className="text-xs font-normal text-muted bg-white/5 px-2 py-0.5 rounded-full">{games?.length || 0} Games</span>
                    </h2>
                    
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => shiftSelectedDate(-1)}
                            className="p-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors"
                            title="Previous Day"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <select
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                            className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-lg text-sm font-medium"
                        >
                            {displayedDates.length > 0 ? (
                                displayedDates.map(date => (
                                    <option key={date} value={date}>
                                        {new Date(date).toLocaleDateString('en-US', { 
                                            month: 'short', 
                                            day: 'numeric',
                                            year: 'numeric'
                                        })}
                                    </option>
                                ))
                            ) : (
                                <option value={selectedDate}>
                                    {new Date(selectedDate).toLocaleDateString('en-US', { 
                                        month: 'short', 
                                        day: 'numeric',
                                        year: 'numeric'
                                    })}
                                </option>
                            )}
                        </select>
                        <button
                            onClick={() => shiftSelectedDate(1)}
                            className="p-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors"
                            title="Next Day"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>

                {games && games.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {games.map((game) => (
                            <GameCard key={game.id} game={game} />
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-16 text-muted border border-dashed border-white/10 rounded-xl">
                        <Calendar size={32} className="mx-auto mb-3 opacity-20" />
                        <p>No games scheduled for {new Date(selectedDate).toLocaleDateString('en-US', { 
                            month: 'long', 
                            day: 'numeric',
                            year: 'numeric'
                        })}</p>
                    </div>
                )}
            </div>
        </div>
    );
};
