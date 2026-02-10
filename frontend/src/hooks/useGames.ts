import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGames, fetchRecommendations, generateRecommendations, Game, Recommendation } from "../api";

export const useGames = () => {
    return useQuery<Game[]>({
        queryKey: ["games"],
        queryFn: fetchGames,
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
