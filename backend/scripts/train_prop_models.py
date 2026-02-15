#!/usr/bin/env python3
"""
Train multi-season player-prop models and report market hit-rates.

Markets:
- PTS
- PRA
- PR
- PA
- RA
- STOCKS

Training data:
- Uses player game logs from 2023-24, 2024-25, 2025-26 seasons.
- Builds rolling-history features per player.
- Trains a regressor per market and evaluates directional hit-rate.

Reports:
1) proxy_line_hit_rate: backtest versus rolling proxy lines (full sample)
2) real_line_hit_rate: backtest versus real sportsbook lines when available
"""

import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from statistics import median
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models
from app.database import SessionLocal


SEASONS = ("2023-24", "2024-25", "2025-26")
MARKETS = ("PTS", "PRA", "PR", "PA", "RA", "STOCKS")
RANDOM_SEED = 42

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


def season_bounds(season: str) -> Tuple[date, date]:
    start_year = int(season.split("-")[0])
    return date(start_year, 7, 1), date(start_year + 1, 7, 1)


def season_for_date(game_date: date) -> str:
    start_year = game_date.year if game_date.month >= 7 else game_date.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def market_value(stat: models.PlayerStats, market: str) -> float:
    pts = float(stat.points or 0.0)
    reb = float(stat.rebounds or 0.0)
    ast = float(stat.assists or 0.0)
    stl = float(stat.steals or 0.0)
    blk = float(stat.blocks or 0.0)

    if market == "PTS":
        return pts
    if market == "PRA":
        return pts + reb + ast
    if market == "PR":
        return pts + reb
    if market == "PA":
        return pts + ast
    if market == "RA":
        return reb + ast
    if market == "STOCKS":
        return stl + blk
    return 0.0


def map_prop_type_to_market(prop_type: Optional[str]) -> Optional[str]:
    key = (prop_type or "").strip().lower()
    if key == "points":
        return "PTS"
    if key in ("pts+reb+ast", "pra"):
        return "PRA"
    if key in ("pts+reb", "pr"):
        return "PR"
    if key in ("pts+ast", "pa"):
        return "PA"
    if key in ("reb+ast", "ra"):
        return "RA"
    if key == "stocks":
        return "STOCKS"
    return None


def safe_mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def safe_std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(np.std(values))


@dataclass
class Sample:
    market: str
    player_id: int
    game_date: date
    features: Dict[str, float]
    target_value: float
    proxy_line: float


def load_team_defense_maps(db: Session):
    abbr_by_team_id = {}
    team_rows = db.query(models.Team.id, models.Team.name).all()
    for team_id, name in team_rows:
        abbr = TEAM_ABBR_BY_NAME.get(name)
        if abbr:
            abbr_by_team_id[team_id] = abbr

    defense_by_season_abbr = {}
    for row in db.query(models.TeamDefenseStats).all():
        abbr = abbr_by_team_id.get(row.team_id)
        if not abbr:
            continue
        defense_by_season_abbr[(row.season, abbr)] = row

    season_avg = defaultdict(lambda: {"pts": [], "reb": [], "ast": []})
    for (season, _abbr), d in defense_by_season_abbr.items():
        if d.allowed_points is not None:
            season_avg[season]["pts"].append(float(d.allowed_points))
        if d.allowed_rebounds is not None:
            season_avg[season]["reb"].append(float(d.allowed_rebounds))
        if d.allowed_assists is not None:
            season_avg[season]["ast"].append(float(d.allowed_assists))

    season_defaults = {}
    for season in SEASONS:
        vals = season_avg.get(season, {"pts": [], "reb": [], "ast": []})
        season_defaults[season] = {
            "opp_allowed_pts": safe_mean(vals["pts"]) or 114.0,
            "opp_allowed_reb": safe_mean(vals["reb"]) or 44.0,
            "opp_allowed_ast": safe_mean(vals["ast"]) or 25.0,
        }

    return defense_by_season_abbr, season_defaults


def build_samples(db: Session) -> Dict[str, List[Sample]]:
    min_date = season_bounds(SEASONS[0])[0]
    max_date = season_bounds(SEASONS[-1])[1]

    defense_map, season_defaults = load_team_defense_maps(db)

    player_rows = db.query(models.Player.id, models.Player.position).all()
    position_by_player = {pid: (pos or "") for pid, pos in player_rows}

    stats_rows = (
        db.query(models.PlayerStats)
        .filter(
            models.PlayerStats.game_date >= min_date,
            models.PlayerStats.game_date < max_date,
        )
        .order_by(models.PlayerStats.player_id.asc(), models.PlayerStats.game_date.asc())
        .all()
    )

    by_player = defaultdict(list)
    for row in stats_rows:
        by_player[row.player_id].append(row)

    market_samples: Dict[str, List[Sample]] = {m: [] for m in MARKETS}

    for player_id, rows in by_player.items():
        if len(rows) < 18:
            continue

        for idx in range(12, len(rows)):
            current = rows[idx]
            history = rows[:idx]
            if len(history) < 12:
                continue

            season = season_for_date(current.game_date)
            if season not in SEASONS:
                continue

            opponent_abbr = (current.opponent or "").upper().strip()
            opp_def = defense_map.get((season, opponent_abbr))
            season_def = season_defaults[season]

            for market in MARKETS:
                hist_values = [market_value(s, market) for s in history]
                if len(hist_values) < 12:
                    continue

                last5 = hist_values[-5:]
                last10 = hist_values[-10:]
                last20 = hist_values[-20:]
                season_avg = safe_mean(hist_values)
                line_proxy = round(safe_mean(last10) * 2) / 2.0
                target = market_value(current, market)

                opp_allowed_pts = float(opp_def.allowed_points) if opp_def and opp_def.allowed_points is not None else season_def["opp_allowed_pts"]
                opp_allowed_reb = float(opp_def.allowed_rebounds) if opp_def and opp_def.allowed_rebounds is not None else season_def["opp_allowed_reb"]
                opp_allowed_ast = float(opp_def.allowed_assists) if opp_def and opp_def.allowed_assists is not None else season_def["opp_allowed_ast"]

                days_rest = (current.game_date - history[-1].game_date).days if history else 2
                is_b2b = 1.0 if days_rest <= 1 else 0.0
                pos = position_by_player.get(player_id, "")

                features = {
                    "line_proxy": float(line_proxy),
                    "last5_avg": safe_mean(last5),
                    "last10_avg": safe_mean(last10),
                    "last20_avg": safe_mean(last20),
                    "season_avg": season_avg,
                    "last5_std": safe_std(last5),
                    "last10_std": safe_std(last10),
                    "trend_last5_minus_last10": safe_mean(last5) - safe_mean(last10),
                    "minutes_last5_avg": safe_mean([float(s.minutes_played or 0.0) for s in history[-5:]]),
                    "minutes_last10_avg": safe_mean([float(s.minutes_played or 0.0) for s in history[-10:]]),
                    "days_rest": float(max(days_rest, 0)),
                    "is_b2b": is_b2b,
                    "opp_allowed_pts": opp_allowed_pts,
                    "opp_allowed_reb": opp_allowed_reb,
                    "opp_allowed_ast": opp_allowed_ast,
                    "is_guard": 1.0 if ("G" in pos) else 0.0,
                    "is_big": 1.0 if ("C" in pos or "F" in pos) else 0.0,
                }

                market_samples[market].append(
                    Sample(
                        market=market,
                        player_id=player_id,
                        game_date=current.game_date,
                        features=features,
                        target_value=float(target),
                        proxy_line=float(line_proxy),
                    )
                )

    return market_samples


def load_real_lines(db: Session) -> Dict[Tuple[int, date, str], float]:
    line_buckets: Dict[Tuple[int, date, str], List[float]] = defaultdict(list)

    rows = (
        db.query(
            models.PlayerProps.player_id,
            models.PlayerProps.prop_type,
            models.PlayerProps.line,
            models.Game.game_date,
        )
        .join(models.Game, models.Game.id == models.PlayerProps.game_id)
        .filter(models.PlayerProps.line.isnot(None))
        .all()
    )

    for player_id, prop_type, line, game_dt in rows:
        market = map_prop_type_to_market(prop_type)
        if market is None:
            continue
        game_date = game_dt.date() if isinstance(game_dt, datetime) else game_dt
        line_buckets[(int(player_id), game_date, market)].append(float(line))

    real_line_map: Dict[Tuple[int, date, str], float] = {}
    for key, values in line_buckets.items():
        real_line_map[key] = float(median(values))
    return real_line_map


def evaluate_hit_rate(pred_values: np.ndarray, actual_values: np.ndarray, lines: np.ndarray) -> Dict[str, float]:
    pred_side = pred_values > lines
    actual_side = actual_values > lines
    push_mask = np.isclose(actual_values, lines)
    valid_mask = ~push_mask

    total = int(valid_mask.sum())
    if total == 0:
        return {"hit_rate": 0.0, "samples": 0, "pushes": int(push_mask.sum())}

    hits = int((pred_side[valid_mask] == actual_side[valid_mask]).sum())
    return {
        "hit_rate": round(hits / total, 4),
        "samples": total,
        "pushes": int(push_mask.sum()),
    }


def train_market_models(db: Session, market_samples: Dict[str, List[Sample]]) -> Dict:
    os.makedirs("/Users/marvens/Desktop/Karchain/backend/models/prop_models", exist_ok=True)
    real_lines = load_real_lines(db)

    report = {
        "generated_at_utc": datetime.utcnow().isoformat(),
        "seasons_used": list(SEASONS),
        "markets": {},
    }

    for market in MARKETS:
        samples = sorted(market_samples.get(market, []), key=lambda s: s.game_date)
        if len(samples) < 200:
            report["markets"][market] = {
                "status": "insufficient_data",
                "samples": len(samples),
            }
            continue

        feature_names = sorted(samples[0].features.keys())
        X = np.array([[s.features[name] for name in feature_names] for s in samples], dtype=np.float32)
        y = np.array([s.target_value for s in samples], dtype=np.float32)
        proxy_lines = np.array([s.proxy_line for s in samples], dtype=np.float32)

        split_idx = int(len(samples) * 0.8)
        if split_idx < 100:
            split_idx = len(samples) - 50

        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        proxy_test = proxy_lines[split_idx:]
        test_samples = samples[split_idx:]

        model = RandomForestRegressor(
            n_estimators=350,
            max_depth=10,
            min_samples_leaf=8,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        mae = float(mean_absolute_error(y_test, preds))
        proxy_eval = evaluate_hit_rate(preds, y_test, proxy_test)

        real_idx = []
        real_lines_list = []
        for i, s in enumerate(test_samples):
            key = (s.player_id, s.game_date, market)
            if key in real_lines:
                real_idx.append(i)
                real_lines_list.append(real_lines[key])

        if real_idx:
            pred_real = preds[real_idx]
            y_real = y_test[real_idx]
            line_real = np.array(real_lines_list, dtype=np.float32)
            real_eval = evaluate_hit_rate(pred_real, y_real, line_real)
        else:
            real_eval = {"hit_rate": 0.0, "samples": 0, "pushes": 0}

        model_path = f"/Users/marvens/Desktop/Karchain/backend/models/prop_models/{market.lower()}_rf.joblib"
        joblib.dump(
            {
                "model": model,
                "feature_names": feature_names,
                "market": market,
                "seasons_trained": list(SEASONS),
            },
            model_path,
        )

        report["markets"][market] = {
            "status": "trained",
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "mae": round(mae, 4),
            "proxy_line_hit_rate": proxy_eval,
            "real_line_hit_rate": real_eval,
            "model_path": model_path,
            "features": feature_names,
        }

    return report


def main():
    db = SessionLocal()
    try:
        market_samples = build_samples(db)
        report = train_market_models(db, market_samples)

        out_path = "/Users/marvens/Desktop/Karchain/backend/data/prop_model_report.json"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(json.dumps(report, indent=2))
        print(f"\nSaved report to: {out_path}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
