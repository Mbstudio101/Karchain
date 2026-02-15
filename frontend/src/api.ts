import axios from "axios";

// Detect if we're in Tauri desktop environment
const isDesktop = typeof window !== 'undefined' && (window as any).__TAURI__ !== undefined;

// Base URL for the FastAPI backend - use localhost for desktop
const API_URL = isDesktop ? "http://localhost:8000" : "http://127.0.0.1:8000";

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

    // Pass client-local context so backend can resolve gameday by user timezone.
    const now = new Date();
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "America/New_York";
    const localDate = now.toLocaleDateString("en-CA"); // YYYY-MM-DD
    const localTime = now.toLocaleTimeString("en-GB", { hour12: false }); // HH:mm:ss
    config.headers["X-Client-Timezone"] = timezone;
    config.headers["X-Client-Local-Date"] = localDate;
    config.headers["X-Client-Local-Time"] = localTime;

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
    additional_props?: Record<string, any> | null;
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

export interface TeamInsight {
    team_id: number;
    team_name: string;
    team_abbr: string;
    conference?: string | null;
    division?: string | null;
    current_record?: string | null;
    logo_url?: string | null;
    games_sampled: number;
    opp_points?: number | null;
    opp_rebounds?: number | null;
    opp_assists?: number | null;
    opp_stocks?: number | null;
    points_rank_most_allowed?: number | null;
    rebounds_rank_most_allowed?: number | null;
    assists_rank_most_allowed?: number | null;
    stocks_rank_most_allowed?: number | null;
    overall_easiest_rank?: number | null;
    strengths: string[];
    weaknesses: string[];
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
    reasoning: string | null;
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

export const fetchGames = async (date?: string): Promise<Game[]> => {
    const params = date ? { date } : {};
    const { data } = await api.get("/games/", { params });
    return data;
};

export const fetchAvailableDates = async (): Promise<string[]> => {
    const { data } = await api.get<string[]>("/games/available-dates");
    return data;
};

export const fetchRecommendations = async (): Promise<Recommendation[]> => {
    const { data } = await api.get("/recommendations/");
    return data;
};

export const fetchTeamInsights = async (): Promise<TeamInsight[]> => {
    const { data } = await api.get<TeamInsight[]>("/teams/insights");
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
    team_name?: string;
    team_logo?: string;
    opponent?: string;
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
    date_used?: string;
}

export const fetchAdvancedProps = async (minEv: number = 0, minKelly: number = 0, date?: string, overUnder?: string): Promise<AdvancedPropsResponse> => {
    const dateParam = date ? `&date=${date}` : '';
    const overUnderParam = overUnder ? `&over_under=${overUnder}` : '';
    const { data } = await api.get(`/recommendations/advanced-props?min_ev=${minEv}&min_kelly=${minKelly}${dateParam}${overUnderParam}`);
    return data;
};

// Genius Picks
export interface GeniusPick {
    player: string;
    player_headshot?: string;
    team?: {
        name: string;
        logo: string;
    };
    prop: string;
    line: number;
    pick: string;
    odds: number;
    sportsbook?: string;
    ev: string;
    edge: string;
    kelly_bet: string;
    hit_rate: string;
    streak: string;
    confidence_range: string;
    grade: string;
    bp_star_rating?: number | null;
    bp_agrees?: boolean;
    opponent_adjusted?: boolean;
    is_b2b?: boolean;
    weighted_projection?: number | null;
}

export interface GeniusPicksResponse {
    genius_count: number;
    picks: GeniusPick[];
    date_used?: string;
}

export const fetchGeniusPicks = async (date?: string): Promise<GeniusPicksResponse> => {
    const dateParam = date ? `?date=${date}` : '';
    const { data } = await api.get<GeniusPicksResponse>(`/recommendations/genius-picks${dateParam}`);
    return data;
};

// Mixed Parlay
export interface ParlayLeg {
    game_id: number;
    pick: string;
    odds: number;
    confidence: number;
    player_name?: string | null;
    player_headshot?: string | null;
    opponent?: string | null;
    matchup?: string | null;
}

export interface ParlayResponse {
    legs: ParlayLeg[];
    combined_odds: number;
    potential_payout: number;
    confidence_score: number;
    date_used?: string;
}

export const fetchMixedParlay = async (legs: number, riskLevel: string = "balanced", date?: string): Promise<ParlayResponse> => {
    let url = `/recommendations/generate-mixed-parlay?legs=${legs}&risk_level=${riskLevel}`;
    if (date) {
        url += `&date=${date}`;
    }
    const { data } = await api.post<ParlayResponse>(url);
    return data;
};

export const fetchParlay = async (legs: number = 3): Promise<ParlayResponse> => {
    const { data } = await api.post<ParlayResponse>(`/recommendations/generate-parlay?legs=${legs}`);
    return data;
};
