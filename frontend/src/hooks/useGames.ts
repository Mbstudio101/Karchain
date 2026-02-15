import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGames, fetchRecommendations, generateRecommendations, Game, Recommendation } from "../api";
import { useEffect } from "react";
import { useWebSocketContext } from "../context/WebSocketContext";

export const useGames = (date?: string) => {
    const queryClient = useQueryClient();
    const { sendMessage } = useWebSocketContext();

    // Subscribe to updates when component mounts
    useEffect(() => {
        const handleGamesUpdate = (event: CustomEvent) => {
            console.log("🏀 Games updated via WebSocket", event.detail);
            queryClient.invalidateQueries({ queryKey: ["games"] });
        };

        window.addEventListener('gamesUpdated', handleGamesUpdate as EventListener);
        
        // Request subscription
        sendMessage({ type: "subscribe", data_type: "games" });

        return () => {
            window.removeEventListener('gamesUpdated', handleGamesUpdate as EventListener);
        };
    }, [queryClient, sendMessage]);

    return useQuery<Game[]>({
        queryKey: ["games", date],
        queryFn: () => fetchGames(date),
        refetchInterval: (query) => {
            // If any game is Live, refresh every 15s for real-time scores
            const games = query.state.data as Game[] | undefined;
            const hasLive = games?.some(g => g.status === "Live");
            return hasLive ? 15000 : 30000;
        },
    });
};

export const useRecommendations = () => {
    return useQuery<Recommendation[]>({
        queryKey: ["recommendations"],
        queryFn: fetchRecommendations,
        refetchInterval: 30000,
    });
};

export const useGenerateRecommendations = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: generateRecommendations,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["recommendations"] });
        }
    });
}
