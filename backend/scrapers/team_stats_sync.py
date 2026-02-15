import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, Optional

from nba_api.stats.endpoints import leaguedashteamstats
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal

logger = logging.getLogger(__name__)

TEAM_ABBR_BY_NAME: Dict[str, str] = {
    "Atlanta Hawks": "ATL",
    "Boston Celtics": "BOS",
    "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA",
    "Chicago Bulls": "CHI",
    "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL",
    "Denver Nuggets": "DEN",
    "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW",
    "Houston Rockets": "HOU",
    "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC",
    "Los Angeles Lakers": "LAL",
    "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA",
    "Milwaukee Bucks": "MIL",
    "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP",
    "New York Knicks": "NYK",
    "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL",
    "Philadelphia 76ers": "PHI",
    "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR",
    "Sacramento Kings": "SAC",
    "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR",
    "Utah Jazz": "UTA",
    "Washington Wizards": "WAS",
}

TEAM_NAME_BY_ABBR = {v: k for k, v in TEAM_ABBR_BY_NAME.items()}
POSITION_BUCKETS = ("PG", "SG", "SF", "PF", "C")
TEAM_NAME_ALIASES: Dict[str, str] = {
    "LA Clippers": "Los Angeles Clippers",
}


def _default_season() -> str:
    now = datetime.utcnow()
    # NBA regular season crosses years; before July, still previous-start season.
    start_year = now.year if now.month >= 7 else now.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def _season_date_bounds(season: str) -> tuple:
    """
    Convert season string like '2025-26' into date bounds.
    Uses July 1 to June 30 to cover full NBA season window.
    """
    try:
        start_year = int(season.split("-")[0])
    except Exception:
        now = datetime.utcnow()
        start_year = now.year if now.month >= 7 else now.year - 1
    return date(start_year, 7, 1), date(start_year + 1, 7, 1)


def _rank_desc(metric_by_abbr: Dict[str, float]) -> Dict[str, int]:
    sorted_items = sorted(metric_by_abbr.items(), key=lambda x: x[1], reverse=True)
    return {abbr: idx + 1 for idx, (abbr, _) in enumerate(sorted_items)}


def _rank_asc(metric_by_abbr: Dict[str, float]) -> Dict[str, int]:
    sorted_items = sorted(metric_by_abbr.items(), key=lambda x: x[1])
    return {abbr: idx + 1 for idx, (abbr, _) in enumerate(sorted_items)}


def _top_position(position_value: Optional[str]) -> Optional[str]:
    if not position_value:
        return None
    text = position_value.upper().strip()
    for bucket in POSITION_BUCKETS:
        if bucket in text:
            return bucket
    return None


def sync_team_stats_from_nba(season: Optional[str] = None) -> None:
    """
    Pulls real team base metrics from NBA API and saves to TeamStats.
    """
    season = season or _default_season()
    db = SessionLocal()
    try:
        logger.info(f"Syncing team stats from NBA API for season {season}...")
        endpoint = leaguedashteamstats.LeagueDashTeamStats(
            season=season,
            season_type_all_star="Regular Season",
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Base",
        )
        df = endpoint.get_data_frames()[0]
        if df.empty:
            logger.warning("NBA API returned no team stats rows.")
            return

        teams_by_name = {team.name: team for team in db.query(models.Team).all()}
        synced = 0

        for _, row in df.iterrows():
            team_name = str(row["TEAM_NAME"])
            team_name = TEAM_NAME_ALIASES.get(team_name, team_name)
            team = teams_by_name.get(team_name)
            if not team:
                continue

            team.current_record = f"{int(row['W'])}-{int(row['L'])}"

            existing = (
                db.query(models.TeamStats)
                .filter(
                    models.TeamStats.team_id == team.id,
                    models.TeamStats.season == season,
                )
                .first()
            )
            if existing:
                stats_row = existing
            else:
                stats_row = models.TeamStats(team_id=team.id, season=season)
                db.add(stats_row)

            stats_row.wins = int(row["W"])
            stats_row.losses = int(row["L"])
            stats_row.win_pct = float(row["W_PCT"])
            stats_row.ppg = float(row["PTS"])
            stats_row.plus_minus = float(row["PLUS_MINUS"])
            stats_row.opp_ppg = float(row["PTS"]) - float(row["PLUS_MINUS"])
            stats_row.timestamp = datetime.utcnow()

            synced += 1

        db.commit()
        logger.info(f"Synced team stats for {synced} teams.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed syncing team stats: {exc}")
        raise
    finally:
        db.close()


def sync_team_defense_from_player_logs(season: Optional[str] = None) -> None:
    """
    Builds real defense-vs-opponent metrics from player game logs and saves to TeamDefenseStats.
    """
    season = season or _default_season()
    db: Session = SessionLocal()
    try:
        logger.info("Syncing team defensive allowed stats from player logs...")
        season_start, season_end = _season_date_bounds(season)

        stats_rows = db.query(
            models.PlayerStats.opponent,
            models.PlayerStats.points,
            models.PlayerStats.rebounds,
            models.PlayerStats.assists,
            models.PlayerStats.steals,
            models.PlayerStats.blocks,
            models.PlayerStats.three_pointers,
            models.Player.position,
        ).join(
            models.Player, models.Player.id == models.PlayerStats.player_id
        ).filter(
            models.PlayerStats.game_date >= season_start,
            models.PlayerStats.game_date < season_end,
        ).all()

        if not stats_rows:
            logger.warning("No player logs available; skipping team defense sync.")
            return

        aggregate = defaultdict(
            lambda: {
                "n": 0,
                "pts": 0.0,
                "reb": 0.0,
                "ast": 0.0,
                "stl_blk": 0.0,
                "fg3m": 0.0,
                "pos": {bucket: {"n": 0, "pts": 0.0} for bucket in POSITION_BUCKETS},
            }
        )

        for row in stats_rows:
            abbr = (row.opponent or "").strip().upper()
            if abbr not in TEAM_NAME_BY_ABBR:
                continue
            agg = aggregate[abbr]
            agg["n"] += 1
            agg["pts"] += float(row.points or 0.0)
            agg["reb"] += float(row.rebounds or 0.0)
            agg["ast"] += float(row.assists or 0.0)
            agg["stl_blk"] += float(row.steals or 0.0) + float(row.blocks or 0.0)
            agg["fg3m"] += float(row.three_pointers or 0.0)

            pos = _top_position(row.position)
            if pos:
                agg["pos"][pos]["n"] += 1
                agg["pos"][pos]["pts"] += float(row.points or 0.0)

        pts_map = {abbr: v["pts"] / v["n"] for abbr, v in aggregate.items() if v["n"] > 0}
        reb_map = {abbr: v["reb"] / v["n"] for abbr, v in aggregate.items() if v["n"] > 0}
        ast_map = {abbr: v["ast"] / v["n"] for abbr, v in aggregate.items() if v["n"] > 0}
        stocks_map = {abbr: v["stl_blk"] / v["n"] for abbr, v in aggregate.items() if v["n"] > 0}

        pos_allowed_points = {bucket: {} for bucket in POSITION_BUCKETS}
        for abbr, values in aggregate.items():
            for bucket in POSITION_BUCKETS:
                n = values["pos"][bucket]["n"]
                if n > 0:
                    pos_allowed_points[bucket][abbr] = values["pos"][bucket]["pts"] / n

        # DvP ranks: 1 = best defense (least points allowed by that position)
        pos_ranks_asc = {bucket: _rank_asc(metric) for bucket, metric in pos_allowed_points.items()}

        teams_by_name = {team.name: team for team in db.query(models.Team).all()}
        team_stats_by_id = {
            row.team_id: row
            for row in db.query(models.TeamStats)
            .filter(models.TeamStats.season == season)
            .all()
        }

        synced = 0
        for team_name, abbr in TEAM_ABBR_BY_NAME.items():
            team = teams_by_name.get(team_name)
            if not team:
                continue
            n = aggregate.get(abbr, {}).get("n", 0)
            if n == 0:
                continue

            existing = (
                db.query(models.TeamDefenseStats)
                .filter(
                    models.TeamDefenseStats.team_id == team.id,
                    models.TeamDefenseStats.season == season,
                )
                .first()
            )
            if existing:
                defense_row = existing
            else:
                defense_row = models.TeamDefenseStats(team_id=team.id, season=season)
                db.add(defense_row)

            defense_row.allowed_points = round(pts_map.get(abbr, 0.0), 2)
            defense_row.allowed_rebounds = round(reb_map.get(abbr, 0.0), 2)
            defense_row.allowed_assists = round(ast_map.get(abbr, 0.0), 2)
            defense_row.allowed_three_pointers = round(
                aggregate[abbr]["fg3m"] / n if n else 0.0, 2
            )

            defense_row.pg_points_rank = pos_ranks_asc["PG"].get(abbr)
            defense_row.sg_points_rank = pos_ranks_asc["SG"].get(abbr)
            defense_row.sf_points_rank = pos_ranks_asc["SF"].get(abbr)
            defense_row.pf_points_rank = pos_ranks_asc["PF"].get(abbr)
            defense_row.c_points_rank = pos_ranks_asc["C"].get(abbr)

            ts = team_stats_by_id.get(team.id)
            defense_row.def_rating = ts.opp_ppg if ts else None
            defense_row.pace = None
            defense_row.timestamp = datetime.utcnow()
            synced += 1

        db.commit()
        logger.info(f"Synced defensive allowed metrics for {synced} teams.")
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed syncing team defense stats: {exc}")
        raise
    finally:
        db.close()


def sync_all_team_metrics(season: Optional[str] = None) -> None:
    season = season or _default_season()
    sync_team_stats_from_nba(season=season)
    sync_team_defense_from_player_logs(season=season)
