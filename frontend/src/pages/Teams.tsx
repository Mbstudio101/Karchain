import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchTeamInsights, TeamInsight } from "../api";
import { ShieldAlert, ShieldCheck, Search, Trophy } from "lucide-react";

const formatVal = (value?: number | null) => (typeof value === "number" ? value.toFixed(1) : "--");

const TeamCard: React.FC<{ team: TeamInsight }> = ({ team }) => {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#0d1a3d]/75 backdrop-blur-md p-4 shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          {team.logo_url ? (
            <img src={team.logo_url} alt={team.team_name} className="w-10 h-10 object-contain rounded-full bg-white/5 p-1" />
          ) : (
            <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-xs font-bold text-secondary">
              {team.team_abbr || team.team_name.slice(0, 3).toUpperCase()}
            </div>
          )}
          <div className="min-w-0">
            <div className="text-white font-semibold truncate">{team.team_name}</div>
            <div className="text-xs text-muted">{team.current_record || "Record N/A"} • Games {team.games_sampled}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[10px] uppercase tracking-[0.12em] text-muted">Overall</div>
          <div className="text-secondary font-bold">#{team.overall_easiest_rank ?? "--"}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-4 gap-2 text-center">
        <div className="rounded-lg bg-black/25 border border-white/10 p-2">
          <div className="text-[10px] text-muted">Opp PTS</div>
          <div className="text-sm font-bold text-white">{formatVal(team.opp_points)}</div>
          <div className="text-[10px] text-secondary">#{team.points_rank_most_allowed ?? "--"}</div>
        </div>
        <div className="rounded-lg bg-black/25 border border-white/10 p-2">
          <div className="text-[10px] text-muted">Opp REB</div>
          <div className="text-sm font-bold text-white">{formatVal(team.opp_rebounds)}</div>
          <div className="text-[10px] text-secondary">#{team.rebounds_rank_most_allowed ?? "--"}</div>
        </div>
        <div className="rounded-lg bg-black/25 border border-white/10 p-2">
          <div className="text-[10px] text-muted">Opp AST</div>
          <div className="text-sm font-bold text-white">{formatVal(team.opp_assists)}</div>
          <div className="text-[10px] text-secondary">#{team.assists_rank_most_allowed ?? "--"}</div>
        </div>
        <div className="rounded-lg bg-black/25 border border-white/10 p-2">
          <div className="text-[10px] text-muted">Opp Stocks</div>
          <div className="text-sm font-bold text-white">{formatVal(team.opp_stocks)}</div>
          <div className="text-[10px] text-secondary">#{team.stocks_rank_most_allowed ?? "--"}</div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg border border-emerald-400/25 bg-emerald-500/10 p-2">
          <div className="flex items-center gap-1 text-emerald-300 text-xs font-semibold mb-1">
            <ShieldCheck size={13} />
            Strengths
          </div>
          <div className="text-xs text-emerald-100/90">
            {team.strengths.length ? team.strengths.join(", ") : "No clear edge yet"}
          </div>
        </div>
        <div className="rounded-lg border border-rose-400/25 bg-rose-500/10 p-2">
          <div className="flex items-center gap-1 text-rose-300 text-xs font-semibold mb-1">
            <ShieldAlert size={13} />
            Weaknesses
          </div>
          <div className="text-xs text-rose-100/90">
            {team.weaknesses.length ? team.weaknesses.join(", ") : "No clear leak yet"}
          </div>
        </div>
      </div>
    </div>
  );
};

export const Teams: React.FC = () => {
  const [query, setQuery] = useState("");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["teamInsights"],
    queryFn: fetchTeamInsights,
    staleTime: 1000 * 60 * 5,
  });

  const filtered = useMemo(() => {
    const list = data || [];
    const q = query.trim().toLowerCase();
    if (!q) return list;
    return list.filter(
      (team) =>
        team.team_name.toLowerCase().includes(q) ||
        team.team_abbr.toLowerCase().includes(q),
    );
  }, [data, query]);

  const topEasiest = (data || []).slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Team Matchup Center</h1>
          <p className="text-muted text-sm mt-1">Opponent stats allowed, team weaknesses/strengths, and easiest rankings.</p>
        </div>
        <div className="relative w-full md:w-80">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search team..."
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-white/10 bg-black/25 text-sm text-white placeholder:text-muted focus:outline-none focus:border-primary/60"
          />
        </div>
      </div>

      <div className="rounded-2xl border border-secondary/30 bg-linear-to-r from-secondary/12 via-transparent to-primary/12 p-4">
        <div className="flex items-center gap-2 text-secondary font-semibold text-sm mb-3">
          <Trophy size={16} />
          Easiest Teams To Target (Overall)
        </div>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-2">
          {topEasiest.map((team) => (
            <div key={team.team_id} className="rounded-lg border border-white/10 bg-black/25 p-2">
              <div className="text-xs text-muted">#{team.overall_easiest_rank ?? "--"}</div>
              <div className="text-sm font-semibold text-white truncate">{team.team_abbr}</div>
              <div className="text-[11px] text-muted truncate">{team.team_name}</div>
            </div>
          ))}
        </div>
      </div>

      {isLoading && <div className="text-sm text-muted">Loading teams insight...</div>}
      {isError && <div className="text-sm text-rose-300">Failed to load teams insight.</div>}

      {!isLoading && !isError && (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {filtered.map((team) => (
            <TeamCard key={team.team_id} team={team} />
          ))}
        </div>
      )}
    </div>
  );
};
