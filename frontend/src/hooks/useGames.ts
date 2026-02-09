import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchGames, fetchRecommendations, generateRecommendations, Game, Recommendation } from "../api";

export const useGames = () => {
    return useQuery<Game[]>({
        queryKey: ["games"],
        queryFn: fetchGames,
        refetchInterval: 30000, // Refresh every 30s
    });
};

export const useRecommendations = () => {
    return useQuery<Recommendation[]>({
        queryKey: ["recommendations"],
        queryFn: fetchRecommendations,
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
