import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGames, fetchRecommendations, generateRecommendations, Game, Recommendation } from "../api";
import { useEffect, useRef } from "react";
import { useWebSocketContext } from "../context/WebSocketContext";

export const useGames = (date?: string) => {
    const queryClient = useQueryClient();
    const { sendMessage } = useWebSocketContext();
    const invalidateTimer = useRef<number | null>(null);

    // Subscribe to updates when component mounts
    useEffect(() => {
        const handleGamesUpdate = (event: CustomEvent) => {
            console.log("🏀 Games updated via WebSocket", event.detail);
            if (invalidateTimer.current) {
                window.clearTimeout(invalidateTimer.current);
            }
            invalidateTimer.current = window.setTimeout(() => {
                queryClient.invalidateQueries({ queryKey: ["games"] });
            }, 250);
        };

        window.addEventListener('gamesUpdated', handleGamesUpdate as EventListener);
        
        // Request subscription
        sendMessage({ type: "subscribe", data_type: "games" });

        return () => {
            window.removeEventListener('gamesUpdated', handleGamesUpdate as EventListener);
            if (invalidateTimer.current) {
                window.clearTimeout(invalidateTimer.current);
            }
        };
    }, [queryClient, sendMessage]);

    return useQuery<Game[]>({
        queryKey: ["games", date],
        queryFn: () => fetchGames(date),
        staleTime: 1000 * 20,
        refetchOnWindowFocus: false,
        retry: 1,
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
        staleTime: 1000 * 30,
        refetchOnWindowFocus: false,
        retry: 1,
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
