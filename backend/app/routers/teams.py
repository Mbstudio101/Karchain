from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List
from .. import models, schemas
from ..dependencies import get_db
from scrapers.team_stats_sync import sync_all_team_metrics

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

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

def _rank_desc(rows: List[dict], metric_key: str) -> Dict[int, int]:
    ranked = sorted(
        [row for row in rows if row.get(metric_key) is not None],
        key=lambda x: x[metric_key],
        reverse=True,
    )
    out: Dict[int, int] = {}
    for i, row in enumerate(ranked, start=1):
        out[row["team_id"]] = i
    return out

def _build_team_tags(row: dict) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []

    metric_labels = [
        ("points_rank_most_allowed", "points"),
        ("rebounds_rank_most_allowed", "rebounds"),
        ("assists_rank_most_allowed", "assists"),
        ("stocks_rank_most_allowed", "stocks"),
    ]

    for key, label in metric_labels:
        rank = row.get(key)
        if rank is None:
            continue
        if rank <= 5:
            weaknesses.append(f"gives up {label}")
        if rank >= 26:
            strengths.append(f"limits {label}")

    return strengths[:3], weaknesses[:3]

@router.get("/", response_model=List[schemas.TeamBase])
def read_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    teams = db.query(models.Team).offset(skip).limit(limit).all()
    return teams

@router.get("/insights", response_model=List[schemas.TeamInsightBase])
def read_team_insights(db: Session = Depends(get_db)):
    teams = db.query(models.Team).all()
    if not teams:
        return []

    # Ensure real tables are populated before serving insights.
    has_team_stats = db.query(models.TeamStats).count() > 0
    has_team_defense = db.query(models.TeamDefenseStats).count() > 0
    if not (has_team_stats and has_team_defense):
        sync_all_team_metrics()
        db.expire_all()

    team_stats_rows = db.query(models.TeamStats).order_by(models.TeamStats.timestamp.desc()).all()
    team_def_rows = db.query(models.TeamDefenseStats).order_by(models.TeamDefenseStats.timestamp.desc()).all()

    if not team_stats_rows or not team_def_rows:
        raise HTTPException(status_code=503, detail="Team metrics are not synced yet. Try again shortly.")

    latest_team_stats_by_team: Dict[int, models.TeamStats] = {}
    for row in team_stats_rows:
        if row.team_id not in latest_team_stats_by_team:
            latest_team_stats_by_team[row.team_id] = row

    latest_team_def_by_team: Dict[int, models.TeamDefenseStats] = {}
    for row in team_def_rows:
        if row.team_id not in latest_team_def_by_team:
            latest_team_def_by_team[row.team_id] = row

    stocks_rows = db.query(
        models.PlayerStats.opponent,
        models.PlayerStats.steals,
        models.PlayerStats.blocks,
    ).all()
    stocks_agg: Dict[str, Dict[str, float]] = {}
    for row in stocks_rows:
        opp = (row.opponent or "").strip().upper()
        if not opp:
            continue
        current = stocks_agg.setdefault(opp, {"n": 0.0, "sum": 0.0})
        current["n"] += 1.0
        current["sum"] += float(row.steals or 0.0) + float(row.blocks or 0.0)

    rows: List[dict] = []
    for team in teams:
        abbr = TEAM_ABBR_BY_NAME.get(team.name, "")
        ts = latest_team_stats_by_team.get(team.id)
        td = latest_team_def_by_team.get(team.id)
        samples = int((ts.wins or 0) + (ts.losses or 0)) if ts else 0
        stock_row = stocks_agg.get(abbr, {"n": 0.0, "sum": 0.0})
        stocks = round(stock_row["sum"] / stock_row["n"], 2) if stock_row["n"] else None
        row = {
            "team_id": team.id,
            "team_name": team.name,
            "team_abbr": abbr,
            "conference": team.conference,
            "division": team.division,
            "current_record": team.current_record,
            "logo_url": team.logo_url,
            "games_sampled": samples,
            "opp_points": td.allowed_points if td else None,
            "opp_rebounds": td.allowed_rebounds if td else None,
            "opp_assists": td.allowed_assists if td else None,
            "opp_stocks": stocks,
        }
        rows.append(row)

    points_rank = _rank_desc(rows, "opp_points")
    rebounds_rank = _rank_desc(rows, "opp_rebounds")
    assists_rank = _rank_desc(rows, "opp_assists")
    stocks_rank = _rank_desc(rows, "opp_stocks")

    overall_score = []
    for row in rows:
        ranks = [
            points_rank.get(row["team_id"]),
            rebounds_rank.get(row["team_id"]),
            assists_rank.get(row["team_id"]),
            stocks_rank.get(row["team_id"]),
        ]
        valid_ranks = [rank for rank in ranks if rank is not None]
        if not valid_ranks:
            continue
        overall_score.append(
            {"team_id": row["team_id"], "score": sum(valid_ranks) / len(valid_ranks)}
        )
    overall_sorted = sorted(overall_score, key=lambda x: x["score"])
    overall_rank_map = {entry["team_id"]: idx + 1 for idx, entry in enumerate(overall_sorted)}

    for row in rows:
        team_id = row["team_id"]
        row["points_rank_most_allowed"] = points_rank.get(team_id)
        row["rebounds_rank_most_allowed"] = rebounds_rank.get(team_id)
        row["assists_rank_most_allowed"] = assists_rank.get(team_id)
        row["stocks_rank_most_allowed"] = stocks_rank.get(team_id)
        row["overall_easiest_rank"] = overall_rank_map.get(team_id)
        strengths, weaknesses = _build_team_tags(row)
        row["strengths"] = strengths
        row["weaknesses"] = weaknesses

    return sorted(
        rows,
        key=lambda x: (x["overall_easiest_rank"] is None, x["overall_easiest_rank"] or 999),
    )

@router.get("/{team_id}", response_model=schemas.TeamBase)
def read_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return team
