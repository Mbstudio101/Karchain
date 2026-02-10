import axios from "axios";

// Base URL for the FastAPI backend
const API_URL = "http://127.0.0.1:8000";

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

// Add interceptor to include JWT in requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const login = async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const { data } = await api.post("/auth/login", formData, {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        }
    });
    return data;
};

export const signup = async (email: string, password: string, fullName?: string) => {
    const { data } = await api.post("/auth/signup", {
        email,
        password,
        full_name: fullName
    });
    return data;
};

export const fetchMe = async () => {
    const { data } = await api.get("/auth/me");
    return data;
};

export interface Odds {
    home_moneyline: number | null;
    away_moneyline: number | null;
    spread_points: number | null;
    home_spread_price: number | null;
    away_spread_price: number | null;
    total_points: number | null;
    over_price: number | null;
    under_price: number | null;
    timestamp: string;
}

export interface TeamStats {
    wins: number;
    losses: number;
    win_pct: number;
    ppg: number;
    opp_ppg: number;
    plus_minus: number;
}

export interface Team {
    id: number;
    name: string;
    sport: string;
    logo_url: string | null;
    current_record?: string | null;
    stats: TeamStats[];
}

export interface Game {
    id: number;
    home_team_id: number;
    away_team_id: number;
    game_date: string;
    venue: string | null;
    status: string;
    home_score: number;
    away_score: number;
    quarter: string | null;
    clock: string | null;
    sport: string;
    home_team: Team;
    away_team: Team;
    odds: Odds[];
    recommendations: Recommendation[];
}

export interface Recommendation {
    id: number;
    game_id: number;
    bet_type: string;
    recommended_pick: string;
    confidence_score: number;
    reasoning: string;
    timestamp: string;
}

export interface Play {
    id: string;
    clock: string;
    text: string;
    type: string;
    scoreValue: number | null;
}

export interface GameTracker {
    game_id: number;
    espn_id: string;
    status: string;
    plays: Play[];
    error?: string;
    message?: string;
}

export const fetchGames = async (): Promise<Game[]> => {
    const { data } = await api.get("/games/");
    return data;
};

export const fetchRecommendations = async (): Promise<Recommendation[]> => {
    const { data } = await api.get("/recommendations/");
    return data;
};

export const generateRecommendations = async (): Promise<Recommendation[]> => {
    const { data } = await api.post("/recommendations/generate");
    return data;
}

export const fetchGameTracker = async (id: string): Promise<GameTracker> => {
    const { data } = await api.get(`/games/${id}/tracker`);
    return data;
};

export interface AdvancedProp {
    prop_id: number;
    player_id: number;
    player_name: string;
    player_position: string | null;
    prop_type: string;
    line: number;
    over_odds: number;
    under_odds: number;
    hit_rate: number;
    weighted_avg: number;
    ev: number;
    edge: number;
    kelly_fraction: number;
    kelly_bet_size: string;
    streak_status: string;
    confidence_level: string;
    recommendation: string;
    sample_size: number;
    confidence_interval: { low: number; high: number };
    grade: string;
    bp_star_rating: number | null;
    bp_ev: number | null;
    bp_agrees: boolean;
    opponent_adjusted: boolean;
    is_b2b: boolean;
}

export interface AdvancedPropsResponse {
    total: number;
    props: AdvancedProp[];
}

export const fetchAdvancedProps = async (minEv: number = 0, minKelly: number = 0): Promise<AdvancedPropsResponse> => {
    const { data } = await api.get(`/recommendations/advanced-props?min_ev=${minEv}&min_kelly=${minKelly}`);
    return data;
};
