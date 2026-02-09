import React from "react";
import { useGames } from "../hooks/useGames";
import { GameCard } from "../components/dashboard/GameCard";
import { RecommendationFeed } from "../components/dashboard/RecommendationFeed";

export const Dashboard: React.FC = () => {
    const { data: games, isLoading, isError } = useGames();

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
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {games?.map((game) => (
                        <GameCard key={game.id} game={game} />
                    ))}
                </div>
            </div>
        </div>
    );
};
