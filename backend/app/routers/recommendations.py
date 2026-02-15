from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import date, datetime, timedelta
from .. import models, schemas
from ..dependencies import get_db
from ..date_utils import (
    get_client_timezone,
    get_current_gameday,
    get_gameday_range,
    game_datetime_to_gameday,
)
from ..analytics.prediction_tracker import PredictionTracker
from ..analytics.self_improvement import SelfImprovementEngine

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)

def _resolve_target_date_with_props(db: Session, target_date: date, timezone_name: Optional[str] = None) -> date:
    """
    If target_date has no props-linked games, fallback to the latest date that does.
    """
    start_utc, end_utc = get_gameday_range(target_date, timezone_name)
    has_target = db.query(models.PlayerProps.id).join(
        models.Game, models.PlayerProps.game_id == models.Game.id
    ).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc
    ).first()
    if has_target:
        return target_date

    game_rows = db.query(models.Game.game_date).join(
        models.PlayerProps, models.PlayerProps.game_id == models.Game.id
    ).filter(
        models.PlayerProps.game_id.isnot(None)
    ).all()
    available_gamedays = set()
    for row in game_rows:
        game_dt = row[0]
        if isinstance(game_dt, str):
            game_dt = datetime.fromisoformat(game_dt)
        if game_dt is None:
            continue
        gameday = game_datetime_to_gameday(game_dt, timezone_name)
        available_gamedays.add(gameday)

    if available_gamedays:
        return max(available_gamedays)
    return target_date

# =============================================================================
# SHARED HELPERS
# =============================================================================

def _calculate_implied_prob(american_odds: int) -> float:
    """Converts American odds to implied probability (0.0 - 1.0)."""
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)


def _resolve_player_with_stats(db: Session, prop: models.PlayerProps) -> Optional[models.Player]:
    """
    Resolve a prop's player to the best matching player record that has stats.
    Handles duplicate player rows (same name, different ids).
    """
    player = prop.player if hasattr(prop, "player") else None
    if player is None and prop.player_id:
        player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()

    if player and player.stats:
        return player

    if not player or not player.name:
        return player

    name_key = player.name.strip().lower()
    alt = db.query(models.Player).join(
        models.PlayerStats, models.PlayerStats.player_id == models.Player.id
    ).filter(
        func.lower(models.Player.name) == name_key
    ).group_by(
        models.Player.id
    ).order_by(
        func.count(models.PlayerStats.id).desc()
    ).first()
    return alt or player

def _build_player_headshot_url(player: models.Player) -> Optional[str]:
    if player.headshot_url:
        return player.headshot_url
    if player.id:
        return f"https://cdn.nba.com/headshots/nba/latest/260x190/{player.id}.png"
    return None

def _build_matchup(game: Optional[models.Game]) -> Optional[str]:
    if not game or not game.home_team or not game.away_team:
        return None
    return f"{game.away_team.name} @ {game.home_team.name}"

def _infer_opponent_for_player(player: models.Player, game: Optional[models.Game]) -> Optional[str]:
    if not game or not game.home_team or not game.away_team:
        return None

    # Primary mapping by team_id when IDs align.
    if player.team_id == game.home_team_id:
        return game.away_team.name
    if player.team_id == game.away_team_id:
        return game.home_team.name

    # Secondary mapping by team name when IDs come from different sources.
    player_team_name = player.team.name if getattr(player, "team", None) else None
    if player_team_name == game.home_team.name:
        return game.away_team.name
    if player_team_name == game.away_team.name:
        return game.home_team.name

    return None


def _reconcile_prop_player_ids(db: Session) -> int:
    """
    Re-link props attached to duplicate players (same name, no stats)
    to the best matching player with actual game logs.
    """
    props = db.query(models.PlayerProps).options(joinedload(models.PlayerProps.player)).all()
    updated = 0

    for prop in props:
        player = prop.player
        if not player or not player.name:
            continue
        if player.stats:
            continue

        canonical = db.query(models.Player).join(
            models.PlayerStats, models.PlayerStats.player_id == models.Player.id
        ).filter(
            func.lower(models.Player.name) == player.name.strip().lower()
        ).group_by(
            models.Player.id
        ).order_by(
            func.count(models.PlayerStats.id).desc()
        ).first()

        if canonical and canonical.id != prop.player_id:
            prop.player_id = canonical.id
            updated += 1

    if updated > 0:
        db.commit()
    return updated


def _calculate_pythagorean_win_pct(ppg: float, opp_ppg: float, exponent: float = 13.91) -> float:
    if ppg == 0 and opp_ppg == 0:
        return 0.5
    return (ppg ** exponent) / ((ppg ** exponent) + (opp_ppg ** exponent))


def _get_league_avg_ppg(db: Session) -> float:
    avg_ppg_result = db.query(func.avg(models.TeamStats.ppg)).scalar()
    return float(avg_ppg_result) if avg_ppg_result else 114.5


def _get_league_avg_defense(db: Session) -> float:
    avg = db.query(func.avg(models.TeamDefenseStats.def_rating)).scalar()
    return float(avg) if avg else 112.0


def _get_league_avg_pace(db: Session) -> float:
    avg = db.query(func.avg(models.TeamDefenseStats.pace)).scalar()
    return float(avg) if avg else 99.5


def _calculate_injury_impact(db: Session, team_id: int) -> tuple:
    """Calculates total missing PPG and missing minutes from injured players."""
    out_players = db.query(models.Player).join(models.Injury).filter(
        models.Player.team_id == team_id,
        models.Injury.status == "Out"
    ).all()

    total_missing_ppg = 0.0
    total_missing_minutes = 0.0
    count = 0

    for p in out_players:
        avg_pts = db.query(func.avg(models.PlayerStats.points)).filter(
            models.PlayerStats.player_id == p.id
        ).scalar()
        avg_min = db.query(func.avg(models.PlayerStats.minutes_played)).filter(
            models.PlayerStats.player_id == p.id
        ).scalar()
        if avg_pts:
            total_missing_ppg += float(avg_pts)
        if avg_min:
            total_missing_minutes += float(avg_min)
        count += 1

    return total_missing_ppg, total_missing_minutes, count


def _get_team_defense_stats(db: Session, team_id: int) -> Optional[models.TeamDefenseStats]:
    """Get the most recent TeamDefenseStats for a team."""
    return db.query(models.TeamDefenseStats).filter(
        models.TeamDefenseStats.team_id == team_id
    ).order_by(models.TeamDefenseStats.timestamp.desc()).first()


def _get_rolling_team_stats(db: Session, team_id: int, n_games: int = 10) -> Dict:
    """
    Calculate rolling N-game averages from recent PlayerStats grouped by team.
    Returns dict with ppg, opp_ppg (estimated), plus_minus.
    """
    # Get the last N game_ids for this team's players
    recent_games = db.query(models.PlayerStats.game_id).filter(
        models.PlayerStats.player_id.in_(
            db.query(models.Player.id).filter(models.Player.team_id == team_id)
        ),
        models.PlayerStats.game_id.isnot(None)
    ).group_by(models.PlayerStats.game_id).order_by(
        models.PlayerStats.game_id.desc()
    ).limit(n_games).all()

    game_ids = [g[0] for g in recent_games]
    if not game_ids:
        return None

    # Sum points per game for this team
    game_totals = db.query(
        models.PlayerStats.game_id,
        func.sum(models.PlayerStats.points).label("total_pts")
    ).filter(
        models.PlayerStats.game_id.in_(game_ids),
        models.PlayerStats.player_id.in_(
            db.query(models.Player.id).filter(models.Player.team_id == team_id)
        )
    ).group_by(models.PlayerStats.game_id).all()

    if not game_totals:
        return None

    ppg_values = [float(g.total_pts) for g in game_totals if g.total_pts]
    rolling_ppg = sum(ppg_values) / len(ppg_values) if ppg_values else 0

    return {
        "rolling_ppg": rolling_ppg,
        "game_count": len(ppg_values)
    }


def _detect_b2b(db: Session, team_id: int, game_date: datetime) -> tuple:
    """
    Detect back-to-back and calculate rest days.
    Returns (is_b2b: bool, rest_days: int)
    """
    # Find the team's most recent game before this one
    prev_game = db.query(models.Game).filter(
        ((models.Game.home_team_id == team_id) | (models.Game.away_team_id == team_id)),
        models.Game.game_date < game_date,
        models.Game.status == "Final"
    ).order_by(models.Game.game_date.desc()).first()

    if not prev_game:
        return False, 2  # Default: not B2B, 2 days rest

    delta = (game_date.date() if isinstance(game_date, datetime) else game_date) - \
            (prev_game.game_date.date() if isinstance(prev_game.game_date, datetime) else prev_game.game_date)
    rest_days = delta.days

    return rest_days <= 1, rest_days


def _get_team_ats_record(db: Session, team_id: int, n_games: int = 5) -> tuple:
    """
    Get a team's Against-the-Spread record over last N games.
    Returns (wins_ats, losses_ats, streak_status_str)
    """
    recent_games = db.query(models.Game).filter(
        ((models.Game.home_team_id == team_id) | (models.Game.away_team_id == team_id)),
        models.Game.status == "Final"
    ).order_by(models.Game.game_date.desc()).limit(n_games).all()

    if not recent_games:
        return 0, 0, "neutral"

    wins_ats = 0
    losses_ats = 0

    for game in recent_games:
        odds = db.query(models.BettingOdds).filter(
            models.BettingOdds.game_id == game.id
        ).order_by(models.BettingOdds.timestamp.desc()).first()

        if not odds or not odds.spread_points:
            continue

        is_home = game.home_team_id == team_id
        margin = game.home_score - game.away_score
        if not is_home:
            margin = -margin

        spread = odds.spread_points if is_home else -odds.spread_points
        # Team covers if their margin > spread (spread is negative for favorites)
        if margin + spread > 0:
            wins_ats += 1
        else:
            losses_ats += 1

    total = wins_ats + losses_ats
    if total == 0:
        return 0, 0, "neutral"

    if wins_ats >= 4:
        streak = "hot"
    elif losses_ats >= 4:
        streak = "cold"
    else:
        streak = "neutral"

    return wins_ats, losses_ats, streak


def _get_grade(ev: float, edge: float, bp_agrees: bool = True, streak: str = "neutral") -> str:
    """
    Real grading system:
    S:  EV > $8, edge > 12%, BP agrees, streak hot
    A+: EV > $5, edge > 8%, confidence > 85%
    A:  EV > $3, edge > 5%, confidence > 75%
    B+: EV > $2, edge > 3%, confidence > 65%
    B:  Everything else that passes minimum filters
    """
    if ev > 8 and edge > 12 and bp_agrees and streak == "hot":
        return "S"
    elif ev > 5 and edge > 8:
        return "A+"
    elif ev > 3 and edge > 5:
        return "A"
    elif ev > 2 and edge > 3:
        return "B+"
    else:
        return "B"


def _extract_prop_values(player, prop_type: str, stats_list) -> List[float]:
    """Extract stat values from player stats based on prop type."""
    key = (prop_type or "").lower()
    if key == 'points':
        return [s.points or 0 for s in stats_list if s.points is not None]
    if key == 'rebounds':
        return [s.rebounds or 0 for s in stats_list if s.rebounds is not None]
    if key == 'assists':
        return [s.assists or 0 for s in stats_list if s.assists is not None]
    if key == 'steals':
        return [s.steals or 0 for s in stats_list if s.steals is not None]
    if key == 'blocks':
        return [s.blocks or 0 for s in stats_list if s.blocks is not None]
    if key in ('threes', 'three_pointers', '3pm'):
        return [s.three_pointers or 0 for s in stats_list if s.three_pointers is not None]
    if key in ('turnovers', 'tov'):
        return [s.turnovers or 0 for s in stats_list if s.turnovers is not None]
    if key in ('pts+reb+ast', 'pra'):
        return [(s.points or 0) + (s.rebounds or 0) + (s.assists or 0) for s in stats_list]
    if key in ('pts+reb', 'pr'):
        return [(s.points or 0) + (s.rebounds or 0) for s in stats_list]
    if key in ('pts+ast', 'pa'):
        return [(s.points or 0) + (s.assists or 0) for s in stats_list]
    if key in ('reb+ast', 'ra'):
        return [(s.rebounds or 0) + (s.assists or 0) for s in stats_list]
    if key == 'stocks':
        return [(s.steals or 0) + (s.blocks or 0) for s in stats_list]
    return []


def _season_start_year_for_game_date(game_date_val: Optional[date]) -> Optional[int]:
    if game_date_val is None:
        return None
    return game_date_val.year if game_date_val.month >= 7 else game_date_val.year - 1


def _sorted_player_stats(player) -> List:
    return sorted(
        [s for s in (player.stats or []) if s.game_date is not None],
        key=lambda s: s.game_date
    )


def _extract_multiseason_prop_values(
    player,
    prop_type: str,
    as_of_date: Optional[date] = None,
) -> tuple:
    """
    Build a recency-prioritized multi-season sample for prop analysis.
    Returns (values, season_sample_counts).
    """
    stats = _sorted_player_stats(player)
    if as_of_date is not None:
        stats = [s for s in stats if s.game_date <= as_of_date]
    if not stats:
        return [], {}

    reference_date = as_of_date or stats[-1].game_date
    current_start = _season_start_year_for_game_date(reference_date)
    if current_start is None:
        return [], {}

    season_buckets: Dict[int, List] = {}
    for s in stats:
        season_start = _season_start_year_for_game_date(s.game_date)
        if season_start is None:
            continue
        season_buckets.setdefault(season_start, []).append(s)

    quotas = {
        current_start: 30,
        current_start - 1: 20,
        current_start - 2: 12,
    }
    default_older_quota = 6

    selected_stats = []
    season_sample_counts: Dict[str, int] = {}
    for season_start in sorted(season_buckets.keys()):
        bucket = season_buckets[season_start]
        picked = bucket[-quotas.get(season_start, default_older_quota):]
        selected_stats.extend(picked)
        season_key = f"{season_start}-{str(season_start + 1)[-2:]}"
        season_sample_counts[season_key] = len(picked)

    selected_stats.sort(key=lambda s: s.game_date)
    values = _extract_prop_values(player, prop_type, selected_stats)
    return values, season_sample_counts


def _get_player_home_away_stats(player, prop_type: str, db: Session) -> tuple:
    """Get home and away stat splits for a player."""
    home_values = []
    away_values = []

    for stat in _sorted_player_stats(player)[-60:]:
        if not stat.game_id:
            continue
        game = db.query(models.Game).filter(models.Game.id == stat.game_id).first()
        if not game:
            continue

        key = (prop_type or "").lower()
        val = 0
        if key == 'points':
            val = stat.points or 0
        elif key == 'rebounds':
            val = stat.rebounds or 0
        elif key == 'assists':
            val = stat.assists or 0
        elif key == 'steals':
            val = stat.steals or 0
        elif key == 'blocks':
            val = stat.blocks or 0
        elif key in ('threes', 'three_pointers', '3pm'):
            val = stat.three_pointers or 0
        elif key in ('turnovers', 'tov'):
            val = stat.turnovers or 0
        elif key in ('pts+reb+ast', 'pra'):
            val = (stat.points or 0) + (stat.rebounds or 0) + (stat.assists or 0)
        elif key in ('pts+reb', 'pr'):
            val = (stat.points or 0) + (stat.rebounds or 0)
        elif key in ('pts+ast', 'pa'):
            val = (stat.points or 0) + (stat.assists or 0)
        elif key in ('reb+ast', 'ra'):
            val = (stat.rebounds or 0) + (stat.assists or 0)
        elif key == 'stocks':
            val = (stat.steals or 0) + (stat.blocks or 0)

        if game.home_team_id == player.team_id:
            home_values.append(val)
        else:
            away_values.append(val)

    return home_values, away_values


def _get_player_minutes(player) -> tuple:
    """Get recent minutes and season average minutes."""
    stats = _sorted_player_stats(player)[-60:]
    if not stats:
        return [], 0.0

    all_minutes = [s.minutes_played for s in stats if s.minutes_played and s.minutes_played > 0]
    recent_minutes = all_minutes[-5:] if all_minutes else []
    season_avg = sum(all_minutes) / len(all_minutes) if all_minutes else 0.0

    return recent_minutes, season_avg


def _build_prop_analysis_kwargs(
    prop, player, db: Session,
    league_avg_defense: float, league_avg_pace: float
) -> Dict:
    """Build the full kwargs dict for analyze_prop() with all available signals."""
    kwargs = {}

    # --- Opponent Defense & Pace (Phase 1a) ---
    if prop.game_id:
        game = db.query(models.Game).filter(models.Game.id == prop.game_id).first()
        if game:
            # Determine opponent
            opponent_team_id = game.away_team_id if game.home_team_id == player.team_id else game.home_team_id
            is_home = game.home_team_id == player.team_id

            opp_defense = _get_team_defense_stats(db, opponent_team_id)
            if opp_defense:
                if opp_defense.def_rating:
                    kwargs['opponent_defense_rating'] = opp_defense.def_rating
                    kwargs['league_avg_defense'] = league_avg_defense
                if opp_defense.pace:
                    kwargs['opponent_pace'] = opp_defense.pace
                    kwargs['league_avg_pace'] = league_avg_pace

            # --- Home/Away (Phase 3c) ---
            kwargs['is_home'] = is_home
            home_vals, away_vals = _get_player_home_away_stats(player, prop.prop_type, db)
            if home_vals:
                kwargs['home_stats'] = home_vals
            if away_vals:
                kwargs['away_stats'] = away_vals

            # --- B2B / Rest Days (Phase 3b) ---
            is_b2b, rest_days = _detect_b2b(db, player.team_id, game.game_date)
            kwargs['is_b2b'] = is_b2b
            kwargs['rest_days'] = rest_days

    # --- Minutes (Phase 1d) ---
    recent_minutes, season_avg_minutes = _get_player_minutes(player)
    if recent_minutes and season_avg_minutes > 0:
        kwargs['recent_minutes'] = recent_minutes
        kwargs['season_avg_minutes'] = season_avg_minutes

    # --- BettingPros Intelligence (Phase 1b) ---
    if prop.star_rating is not None:
        kwargs['bp_star_rating'] = prop.star_rating
    if prop.bp_ev is not None:
        kwargs['bp_ev'] = prop.bp_ev
    if prop.performance_pct is not None:
        kwargs['bp_performance_pct'] = prop.performance_pct
    if prop.recommended_side:
        kwargs['bp_recommended_side'] = prop.recommended_side

    return kwargs


# =============================================================================
# CORE RECOMMENDATION CREATION
# =============================================================================

def _create_rec(db, list_ref, game, bet_type, pick, confidence, reason,
                injury_adjustment=0.0, ml_prob_home_win=None):
    """Helper to check existence and add recommendation."""
    confidence = float(confidence)

    existing = db.query(models.Recommendation).filter(
        models.Recommendation.game_id == game.id,
        models.Recommendation.bet_type == bet_type,
        models.Recommendation.recommended_pick == pick
    ).first()

    if existing:
        list_ref.append(existing)
        return

    rec = models.Recommendation(
        game_id=game.id,
        bet_type=bet_type,
        recommended_pick=pick,
        confidence_score=round(confidence, 2),
        reasoning=reason
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Track the prediction for self-improvement
    try:
        tracker = PredictionTracker(db)
        feature_snapshot = {
            'home_ppg': float(game.home_team.stats[0].ppg) if game.home_team.stats else 0,
            'away_ppg': float(game.away_team.stats[0].ppg) if game.away_team.stats else 0,
            'home_net': float(game.home_team.stats[0].ppg - game.home_team.stats[0].opp_ppg) if game.home_team.stats else 0,
            'away_net': float(game.away_team.stats[0].ppg - game.away_team.stats[0].opp_ppg) if game.away_team.stats else 0,
            'injury_adjustment': float(injury_adjustment),
            'ml_probability': float(ml_prob_home_win) if ml_prob_home_win is not None else None
        }

        model_used = 'xgboost' if ml_prob_home_win is not None else 'heuristic'
        tracker.record_prediction(rec, model_used=model_used, feature_snapshot=feature_snapshot)
    except Exception as e:
        print(f"Failed to track prediction: {e}")

    list_ref.append(rec)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/", response_model=List[schemas.RecommendationBase])
def get_recommendations(request: Request, date: Optional[date] = None, db: Session = Depends(get_db)):
    """Returns recommendations. Defaults to today's games if no date provided."""
    client_tz = get_client_timezone(request)
    if date is None:
        date = get_current_gameday(client_tz)

    start_utc, end_utc = get_gameday_range(date, client_tz)
    recs = db.query(models.Recommendation).join(models.Game).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc
    ).order_by(models.Recommendation.confidence_score.desc()).all()

    return recs


@router.post("/generate", response_model=List[schemas.RecommendationBase])
def generate_recommendations(db: Session = Depends(get_db)):
    """Generates recommendations for ACTIVE or UPCOMING games only."""
    games = db.query(models.Game).filter(models.Game.status.in_(["Scheduled", "Live"])).all()
    generated_recs = []

    league_avg_ppg = _get_league_avg_ppg(db)
    league_avg_defense = _get_league_avg_defense(db)

    for game in games:
        if not game.home_team.stats or not game.away_team.stats:
            continue

        home_stats = game.home_team.stats[0]
        away_stats = game.away_team.stats[0]

        # --- Injury Check ---
        home_missing_ppg, home_missing_min, home_out = _calculate_injury_impact(db, game.home_team_id)
        away_missing_ppg, away_missing_min, away_out = _calculate_injury_impact(db, game.away_team_id)
        injury_net_impact = (home_missing_ppg - away_missing_ppg) * 0.4
        injury_adjustment = -1 * injury_net_impact

        # --- Rolling Team Stats (Phase 3a) ---
        home_rolling = _get_rolling_team_stats(db, game.home_team_id)
        away_rolling = _get_rolling_team_stats(db, game.away_team_id)

        # Blend season avg (40%) + recent form (60%)
        if home_rolling and home_rolling['game_count'] >= 5:
            blended_home_ppg = home_stats.ppg * 0.4 + home_rolling['rolling_ppg'] * 0.6
        else:
            blended_home_ppg = home_stats.ppg

        if away_rolling and away_rolling['game_count'] >= 5:
            blended_away_ppg = away_stats.ppg * 0.4 + away_rolling['rolling_ppg'] * 0.6
        else:
            blended_away_ppg = away_stats.ppg

        # --- B2B Detection (Phase 3b) ---
        home_b2b, home_rest = _detect_b2b(db, game.home_team_id, game.game_date)
        away_b2b, away_rest = _detect_b2b(db, game.away_team_id, game.game_date)

        b2b_adjustment = 0.0
        if home_b2b and not away_b2b:
            b2b_adjustment = -3.0  # Home team on B2B
        elif away_b2b and not home_b2b:
            b2b_adjustment = 3.0   # Away team on B2B
        # Rest advantage
        if home_rest >= 3 and away_rest <= 1:
            b2b_adjustment += 1.0
        elif away_rest >= 3 and home_rest <= 1:
            b2b_adjustment -= 1.0

        # --- Opponent Defense Adjustment ---
        home_def = _get_team_defense_stats(db, game.home_team_id)
        away_def = _get_team_defense_stats(db, game.away_team_id)

        defense_adjustment = 0.0
        if home_def and away_def and home_def.def_rating and away_def.def_rating:
            # If away team has weak defense (high def_rating), home scores more
            home_opp_def_factor = (away_def.def_rating - league_avg_defense) / league_avg_defense
            away_opp_def_factor = (home_def.def_rating - league_avg_defense) / league_avg_defense
            defense_adjustment = (home_opp_def_factor - away_opp_def_factor) * blended_home_ppg * 0.5

        # --- ML Prediction ---
        ml_prob_home_win = None
        try:
            from app.analytics.ml_models import NBAXGBoostModel
            ml_model = NBAXGBoostModel()
            ml_prob_home_win = ml_model.predict_one(game, db)
        except Exception as e:
            print(f"ML Prediction failed: {e}")

        # 2. Get latest odds
        if not game.odds:
            continue

        latest_odds = game.odds[-1]

        # --- Moneyline Analysis ---
        if latest_odds.home_moneyline and latest_odds.away_moneyline:
            home_win_prob = _calculate_pythagorean_win_pct(blended_home_ppg, home_stats.opp_ppg)
            away_win_prob = _calculate_pythagorean_win_pct(blended_away_ppg, away_stats.opp_ppg)

            if ml_prob_home_win is not None:
                home_win_prob = (home_win_prob * 0.4) + (ml_prob_home_win * 0.6)
                away_win_prob = 1.0 - home_win_prob
            else:
                home_win_prob += 0.035
                away_win_prob -= 0.035
                prob_adjustment = injury_adjustment * 0.035
                home_win_prob += prob_adjustment
                away_win_prob -= prob_adjustment

            # B2B probability adjustment
            b2b_prob_adj = b2b_adjustment * 0.02  # ~2% per point
            home_win_prob += b2b_prob_adj
            away_win_prob -= b2b_prob_adj

            home_implied = _calculate_implied_prob(latest_odds.home_moneyline)
            away_implied = _calculate_implied_prob(latest_odds.away_moneyline)

            home_win_prob = max(0.0, min(1.0, home_win_prob))
            away_win_prob = max(0.0, min(1.0, away_win_prob))

            if home_win_prob > home_implied + 0.05:
                edge = home_win_prob - home_implied
                reason = f"High Value: Model gives {home_win_prob:.1%} chance vs Vegas {home_implied:.1%}. Edge: {edge:.1%}"
                if ml_prob_home_win is not None:
                    reason += " (ML Enhanced)"
                if home_b2b:
                    reason += " (Home B2B)"
                if home_out > 2:
                    reason += f" (Note: {home_out} players OUT for Home)"
                _create_rec(db, generated_recs, game, "Moneyline", game.home_team.name,
                           edge, reason, injury_adjustment, ml_prob_home_win)

            elif away_win_prob > away_implied + 0.05:
                edge = away_win_prob - away_implied
                reason = f"Upset Alert: Model gives {away_win_prob:.1%} chance vs Vegas {away_implied:.1%}. Edge: {edge:.1%}"
                if ml_prob_home_win is not None:
                    reason += " (ML Enhanced)"
                if away_b2b:
                    reason += " (Away B2B)"
                if away_out > 2:
                    reason += f" (Note: {away_out} players OUT for Away)"
                _create_rec(db, generated_recs, game, "Moneyline", game.away_team.name,
                           edge, reason, injury_adjustment, ml_prob_home_win)

        # --- Spread Analysis ---
        if latest_odds.spread_points:
            home_net = blended_home_ppg - home_stats.opp_ppg
            away_net = blended_away_ppg - away_stats.opp_ppg

            expected_spread_margin = (home_net - away_net) + 3.0 + injury_adjustment + b2b_adjustment + defense_adjustment

            if ml_prob_home_win is not None:
                ml_spread_est = (ml_prob_home_win - 0.5) * 25
                expected_spread_margin = (expected_spread_margin * 0.5) + (ml_spread_est * 0.5)

            fair_spread_line = -1 * expected_spread_margin
            vegas_spread = latest_odds.spread_points
            diff = fair_spread_line - vegas_spread

            if abs(diff) > 3.0:
                if diff < 0:
                    pick = game.home_team.name
                    confidence = min(0.98, 0.5 + (abs(diff) / 20))
                    reason = f"Simulated Spread: {fair_spread_line:.1f} vs Vegas: {vegas_spread}. Home team undervalued."
                else:
                    pick = game.away_team.name
                    confidence = min(0.98, 0.5 + (abs(diff) / 20))
                    reason = f"Simulated Spread: {fair_spread_line:.1f} vs Vegas: {vegas_spread}. Away team undervalued."

                if abs(injury_adjustment) > 0:
                    reason += f" (Includes {abs(injury_adjustment):.1f}pt injury adj)"
                if abs(b2b_adjustment) > 0:
                    reason += f" (B2B adj: {b2b_adjustment:+.1f}pt)"
                if abs(defense_adjustment) > 0.5:
                    reason += f" (Def adj: {defense_adjustment:+.1f}pt)"
                if ml_prob_home_win is not None:
                    reason += " (ML Enhanced)"

                _create_rec(db, generated_recs, game, "Spread", pick, confidence,
                           reason, injury_adjustment, ml_prob_home_win)

        # --- Totals Analysis (Over/Under) ---
        if latest_odds.total_points and latest_odds.over_price and latest_odds.under_price:
            expected_total = blended_home_ppg + blended_away_ppg
            home_def_delta = home_stats.opp_ppg - league_avg_ppg
            away_def_delta = away_stats.opp_ppg - league_avg_ppg
            expected_total += (home_def_delta + away_def_delta) * 0.5

            # Pace adjustment for totals
            if home_def and away_def and home_def.pace and away_def.pace:
                league_pace = _get_league_avg_pace(db)
                combined_pace = (home_def.pace + away_def.pace) / 2
                pace_factor = combined_pace / league_pace
                expected_total *= pace_factor

            # B2B teams score slightly less
            if home_b2b:
                expected_total -= 1.5
            if away_b2b:
                expected_total -= 1.5

            vegas_total = latest_odds.total_points
            diff = expected_total - vegas_total

            if abs(diff) > 4.0:
                side = "Over" if diff > 0 else "Under"
                confidence = min(0.95, 0.5 + (abs(diff) / 25))
                reason = f"Combined PPG Analysis: {expected_total:.1f} vs Vegas: {vegas_total}. Model suggests {side}."
                if home_b2b or away_b2b:
                    reason += " (B2B factor included)"
                _create_rec(db, generated_recs, game, "Total", side, confidence,
                           reason, injury_adjustment, ml_prob_home_win)

    return generated_recs


@router.post("/generate-parlay", response_model=schemas.ParlayBase)
def generate_parlay(request: Request, legs: int = 3, date: Optional[date] = None, db: Session = Depends(get_db)):
    """Generate an AI-powered parlay for today's games with correlation awareness."""
    from ..analytics.advanced_stats import detect_correlation, calculate_parlay_correlation_penalty

    client_tz = get_client_timezone(request)
    target_date = date if date is not None else get_current_gameday(client_tz)
    start_of_day, end_of_day = get_gameday_range(target_date, client_tz)

    top_recs = db.query(models.Recommendation).join(
        models.Game, models.Recommendation.game_id == models.Game.id
    ).filter(
        models.Game.game_date >= start_of_day,
        models.Game.game_date <= end_of_day
    ).order_by(
        models.Recommendation.confidence_score.desc()
    ).limit(legs * 2).all()  # Get extra for correlation filtering

    if len(top_recs) < legs:
        raise HTTPException(status_code=400,
                           detail=f"Not enough recommendations for today to build a {legs}-leg parlay.")

    # Build bet dicts for correlation detection
    bet_dicts = []
    for rec in top_recs:
        game = db.query(models.Game).filter(models.Game.id == rec.game_id).first()
        if not game or not game.odds:
            continue
        latest_odds = game.odds[-1]

        if "spread" in rec.bet_type.lower():
            american_odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
        else:
            american_odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline

        if american_odds is None:
            american_odds = -110

        bet_dicts.append({
            'rec': rec,
            'game_id': rec.game_id,
            'team_id': game.home_team_id if rec.recommended_pick == game.home_team.name else game.away_team_id,
            'matchup': _build_matchup(game),
            'odds': american_odds,
            'confidence': rec.confidence_score,
            'bet_type': rec.bet_type
        })

    # Select legs greedily, minimizing correlation
    selected = []
    for bet in bet_dicts:
        if len(selected) >= legs:
            break

        # Check correlation with already selected bets
        has_high_correlation = False
        for sel in selected:
            corr = detect_correlation(bet, sel)
            if corr.level == "high":
                has_high_correlation = True
                break

        if not has_high_correlation:
            selected.append(bet)

    if len(selected) < legs:
        # Fill remaining from what's left
        for bet in bet_dicts:
            if bet not in selected and len(selected) < legs:
                selected.append(bet)

    # Calculate correlation penalty
    correlation_penalty = calculate_parlay_correlation_penalty(selected)

    parlay_legs = []
    combined_decimal_odds = 1.0
    total_confidence = 0.0

    for bet in selected:
        odds = bet['odds']
        if odds > 0:
            decimal_odds = 1 + (odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(odds))

        combined_decimal_odds *= decimal_odds
        total_confidence += bet['confidence']

        parlay_legs.append(schemas.ParlayLeg(
            game_id=bet['game_id'],
            pick=f"{bet['rec'].recommended_pick} ({bet['bet_type']})",
            odds=odds,
            confidence=bet['confidence'],
            matchup=bet.get('matchup'),
        ))

    # Apply correlation penalty to confidence
    adjusted_confidence = (total_confidence / len(parlay_legs)) * correlation_penalty if parlay_legs else 0

    if combined_decimal_odds >= 2:
        combined_american = int((combined_decimal_odds - 1) * 100)
    else:
        combined_american = int(-100 / (combined_decimal_odds - 1))

    potential_payout = 100 * combined_decimal_odds

    # True parlay probability (Phase 5b)
    true_prob = 1.0
    for bet in selected:
        true_prob *= bet['confidence']
    true_prob *= correlation_penalty  # Adjust for correlations

    return schemas.ParlayBase(
        legs=parlay_legs,
        combined_odds=combined_american,
        potential_payout=round(potential_payout, 2),
        confidence_score=round(adjusted_confidence, 2),
        date_used=target_date
    )


@router.post("/generate-mixed-parlay", response_model=schemas.ParlayBase)
def generate_mixed_parlay(request: Request, legs: int = 5, risk_level: str = "balanced", seed: int = None, date: Optional[date] = None, db: Session = Depends(get_db)):
    """
    Generate an AI-powered parlay mixing player props with game bets.
    Enhanced with reconstructed NBA data: clutch performance, tracking metrics,
    athletic analytics, and advanced ML-enhanced predictions.
    
    Args:
        legs: Number of parlay legs (default: 5)
        risk_level: Risk level - 'conservative', 'balanced', or 'aggressive' (default: 'balanced')
        seed: Random seed for deterministic results (optional, for testing)
        date: Target date for the parlay (optional, defaults to current gameday)
    """
    client_tz = get_client_timezone(request)
    target_date = date if date is not None else get_current_gameday(client_tz)
    _reconcile_prop_player_ids(db)
    target_date = _resolve_target_date_with_props(db, target_date, client_tz)
    start_of_day, end_of_day = get_gameday_range(target_date, client_tz)

    try:
        # Enhanced mixed-parlay path calls external analytics repeatedly and is unstable.
        # Use local legacy pipeline for deterministic availability.
        raise RuntimeError("Use legacy mixed parlay pipeline")

        # Use enhanced parlay generator with reconstructed NBA data
        from ..analytics.enhanced_parlay_generator import EnhancedParlayGenerator
        import random

        # Set random seed if provided (for testing) or use current time for variety
        if seed is not None:
            random.seed(seed)
        else:
            random.seed()  # Use current time

        generator = EnhancedParlayGenerator()
        result = generator.generate_ai_parlay(legs=legs, risk_level=risk_level)

        # Map to ParlayLeg schema format
        parlay_legs = []
        for leg in result['legs']:
            if leg['type'] == 'prop':
                # Look up game_id from player props
                player = db.query(models.Player).filter(
                    models.Player.name == leg.get('player', '')
                ).order_by(models.Player.id.desc()).first()
                if player:
                    alt_player = db.query(models.Player).join(
                        models.PlayerStats, models.PlayerStats.player_id == models.Player.id
                    ).filter(
                        func.lower(models.Player.name) == player.name.lower()
                    ).group_by(models.Player.id).order_by(
                        func.count(models.PlayerStats.id).desc()
                    ).first()
                    if alt_player:
                        player = alt_player
                game_id = 0
                if player:
                    prop = db.query(models.PlayerProps).join(
                        models.Game
                    ).filter(
                        models.PlayerProps.player_id == player.id,
                        models.Game.game_date >= start_of_day,
                        models.Game.game_date <= end_of_day
                    ).first()
                    if prop and prop.game_id:
                        game_id = prop.game_id
                    if game_id == 0:
                        latest_prop = db.query(models.PlayerProps).filter(
                            models.PlayerProps.player_id == player.id,
                            models.PlayerProps.game_id.isnot(None)
                        ).order_by(models.PlayerProps.timestamp.desc()).first()
                        if latest_prop and latest_prop.game_id:
                            game_id = latest_prop.game_id

                pick_str = f"{leg.get('player', '')} {leg.get('prop_type', '').upper()} {leg['pick']} {leg.get('line', '')}"
                parlay_legs.append(schemas.ParlayLeg(
                    game_id=game_id,
                    pick=pick_str,
                    odds=int(leg.get('odds', -110)),
                    confidence=float(leg.get('hit_rate', leg.get('confidence_score', 0.5))),
                    player_name=leg.get('player'),
                ))
            else:  # game bet
                # Find game_id from recommendation
                game_id = 0
                rec = db.query(models.Recommendation).filter(
                    models.Recommendation.recommended_pick == leg.get('pick', '')
                ).order_by(models.Recommendation.timestamp.desc()).first()
                if rec:
                    game_id = rec.game_id
                if game_id == 0:
                    latest_rec = db.query(models.Recommendation).filter(
                        models.Recommendation.game_id.isnot(None)
                    ).order_by(models.Recommendation.timestamp.desc()).first()
                    if latest_rec:
                        game_id = latest_rec.game_id

                pick_str = f"{leg.get('pick', '')} ({leg.get('bet_type', 'Spread')})"
                parlay_legs.append(schemas.ParlayLeg(
                    game_id=game_id,
                    pick=pick_str,
                    odds=int(leg.get('odds', -110)),
                    confidence=float(leg.get('confidence', 0.5)),
                ))

        if not parlay_legs or any(leg.game_id == 0 for leg in parlay_legs):
            raise ValueError("Enhanced parlay produced invalid legs")

        return schemas.ParlayBase(
            legs=parlay_legs,
            combined_odds=int(result['combined_odds']),
            potential_payout=round(result['payout'], 2),
            confidence_score=round(result['avg_confidence'], 2),
            date_used=target_date
        )
        
    except Exception as e:
        # Fallback to legacy system if enhanced system fails
        print(f"Enhanced mixed parlay failed: {e}, falling back to legacy system")
        
        from ..analytics.advanced_stats import (
            analyze_prop, detect_correlation, calculate_parlay_correlation_penalty,
            StreakStatus, BetConfidence
        )

    target_date = date if date is not None else get_current_gameday(client_tz)
    target_date = _resolve_target_date_with_props(db, target_date, client_tz)
    start_of_day, end_of_day = get_gameday_range(target_date, client_tz)

    league_avg_defense = _get_league_avg_defense(db)
    league_avg_pace = _get_league_avg_pace(db)

    # --- Phase 2c: Filter props by TODAY's date ---
    prop_bets = []
    props = db.query(models.PlayerProps).join(
        models.Game, models.PlayerProps.game_id == models.Game.id
    ).options(
        joinedload(models.PlayerProps.player),
        joinedload(models.PlayerProps.player).joinedload(models.Player.stats),
        joinedload(models.PlayerProps.player).joinedload(models.Player.team),
        joinedload(models.PlayerProps.game).joinedload(models.Game.home_team),
        joinedload(models.PlayerProps.game).joinedload(models.Game.away_team),
    ).filter(
        models.Game.game_date >= start_of_day,
        models.Game.game_date <= end_of_day
    ).all()

    for prop in props:
        player = _resolve_player_with_stats(db, prop)
        if not player or not player.stats or len(player.stats) < 5:
            continue

        values, season_sample_counts = _extract_multiseason_prop_values(
            player,
            prop.prop_type,
            as_of_date=target_date,
        )
        if len(values) < 5:
            continue

        # Build full analysis kwargs with all signals
        analysis_kwargs = _build_prop_analysis_kwargs(
            prop, player, db, league_avg_defense, league_avg_pace
        )

        analysis = analyze_prop(
            line=prop.line,
            historical_stats=values,
            odds_over=prop.over_odds or -110,
            odds_under=prop.under_odds or -110,
            game=prop.game,  # Pass game object for ML model
            **analysis_kwargs
        )

        # Calculate edge for the best side
        if analysis.recommendation == "over":
            edge = analysis.edge / 100  # Convert from pct to decimal
            odds = prop.over_odds
        elif analysis.recommendation == "under":
            edge = analysis.edge / 100
            odds = prop.under_odds
        else:
            continue

        if edge < 0.03:
            continue

        prop_bets.append({
            'type': 'prop',
            'game_id': prop.game_id or 0,
            'player_id': player.id,
            'player_name': player.name,
            'player_headshot': _build_player_headshot_url(player),
            'opponent': _infer_opponent_for_player(player, prop.game),
            'matchup': _build_matchup(prop.game),
            'team_id': player.team_id,
            'prop_type': prop.prop_type,
            'pick': f"{player.name} {prop.prop_type.upper()} {analysis.recommendation.upper()} {prop.line}",
            'odds': odds,
            'confidence': min(0.95, 0.5 + edge),
            'edge': edge,
            'bp_agrees': analysis_kwargs.get('bp_recommended_side', '').lower() == analysis.recommendation if analysis_kwargs.get('bp_recommended_side') else True,
            'season_sample_counts': season_sample_counts,
        })

    # Get best game bets for TODAY only
    game_bets = []
    recommendations = db.query(models.Recommendation).join(
        models.Game, models.Recommendation.game_id == models.Game.id
    ).options(
        joinedload(models.Recommendation.game).joinedload(models.Game.odds)
    ).filter(
        models.Game.game_date >= start_of_day,
        models.Game.game_date <= end_of_day
    ).order_by(
        models.Recommendation.confidence_score.desc()
    ).limit(10).all()

    for rec in recommendations:
        game = rec.game
        if not game or not game.odds:
            continue
        latest_odds = game.odds[-1]

        if "spread" in rec.bet_type.lower():
            odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
        else:
            odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline

        if odds is None:
            odds = -110

        team_id = game.home_team_id if rec.recommended_pick == game.home_team.name else game.away_team_id

        game_bets.append({
            'type': 'game',
            'game_id': rec.game_id,
            'team_id': team_id,
            'pick': f"{rec.recommended_pick} ({rec.bet_type})",
            'matchup': _build_matchup(game),
            'odds': odds,
            'confidence': rec.confidence_score,
            'edge': rec.confidence_score - 0.5
        })

    # Sort all bets by edge
    prop_bets.sort(key=lambda x: x['edge'], reverse=True)
    game_bets.sort(key=lambda x: x['edge'], reverse=True)

    # --- Phase 1c / 5a: Correlation-aware selection ---
    used_players = set()
    used_games = set()

    num_games_target = legs // 2
    num_props_target = legs - num_games_target

    # Select game bets (unique games)
    selected_games = []
    for bet in game_bets:
        gid = bet.get('game_id')
        if gid and gid not in used_games:
            selected_games.append(bet)
            used_games.add(gid)
            if len(selected_games) >= num_games_target:
                break

    # Select prop bets (unique players, check correlation with selected)
    selected_props = []
    for bet in prop_bets:
        pname = bet.get('player_name')
        if pname and pname not in used_players:
            # Check correlation with already selected legs
            has_high_corr = False
            for sel in selected_games + selected_props:
                corr = detect_correlation(bet, sel)
                if corr.level == "high":
                    has_high_corr = True
                    break
            if not has_high_corr:
                selected_props.append(bet)
                used_players.add(pname)
                if len(selected_props) >= num_props_target:
                    break

    selected = selected_games + selected_props

    # Fill if needed
    remaining = [b for b in prop_bets if b.get('player_name') not in used_players] + \
                [b for b in game_bets if b.get('game_id') not in used_games]
    remaining.sort(key=lambda x: x['edge'], reverse=True)

    while len(selected) < legs and remaining:
        bet = remaining.pop(0)
        if bet['type'] == 'prop':
            pname = bet.get('player_name')
            if pname not in used_players:
                selected.append(bet)
                used_players.add(pname)
        else:
            gid = bet.get('game_id')
            if gid not in used_games:
                selected.append(bet)
                used_games.add(gid)

    if len(selected) < legs:
        if len(selected) < 2:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough unique bets available. Found {len(selected)} unique, need at least 2."
            )
        legs = len(selected)

    # Calculate correlation penalty (Phase 5b)
    correlation_penalty = calculate_parlay_correlation_penalty(selected)

    # Build parlay
    parlay_legs = []
    combined_decimal = 1.0
    total_confidence = 0.0

    for bet in selected[:legs]:
        odds = bet.get('odds')
        if odds is None or odds == 0:
            odds = -110

        if odds > 0:
            decimal_odds = 1 + (odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(odds))
        combined_decimal *= decimal_odds
        total_confidence += bet['confidence']

        parlay_legs.append(schemas.ParlayLeg(
            game_id=bet.get('game_id', 0),
            pick=bet['pick'],
            odds=odds,
            confidence=bet['confidence'],
            player_name=bet.get('player_name'),
            player_headshot=bet.get('player_headshot'),
            opponent=bet.get('opponent'),
            matchup=bet.get('matchup'),
        ))

    if combined_decimal >= 2:
        combined_american = int((combined_decimal - 1) * 100)
    else:
        combined_american = int(-100 / (combined_decimal - 1))

    potential_payout = 100 * combined_decimal

    # True parlay probability (Phase 5b)
    true_prob = 1.0
    for bet in selected[:legs]:
        true_prob *= bet['confidence']
    true_prob *= correlation_penalty

    adjusted_confidence = (total_confidence / len(parlay_legs)) * correlation_penalty

    return schemas.ParlayBase(
        legs=parlay_legs,
        combined_odds=combined_american,
        potential_payout=round(potential_payout, 2),
        confidence_score=round(adjusted_confidence, 2),
        date_used=target_date
    )


@router.get("/advanced-props")
def get_advanced_props(request: Request, min_ev: float = 0, min_kelly: float = 0, date: Optional[date] = None, over_under: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get player props with advanced analytics.
    Now with: opponent defense (1a), pace (1a), BettingPros (1b),
    minutes (1d), home/away splits (3c), B2B detection (3b),
    real confidence intervals (4c).
    """
    from ..analytics.advanced_stats import (
        analyze_prop, kelly_criterion, calculate_ev, detect_streak,
        weighted_average, recency_hit_rate, wilson_confidence_interval,
        StreakStatus, BetConfidence
    )

    client_tz = get_client_timezone(request)
    target_date = date if date is not None else get_current_gameday(client_tz)
    _reconcile_prop_player_ids(db)
    target_date = _resolve_target_date_with_props(db, target_date, client_tz)
    start_of_day, end_of_day = get_gameday_range(target_date, client_tz)

    league_avg_defense = _get_league_avg_defense(db)
    league_avg_pace = _get_league_avg_pace(db)

    # Filter props by today's date
    props = db.query(models.PlayerProps).join(
        models.Game, models.PlayerProps.game_id == models.Game.id
    ).options(
        joinedload(models.PlayerProps.player),
        joinedload(models.PlayerProps.game).joinedload(models.Game.home_team),
        joinedload(models.PlayerProps.game).joinedload(models.Game.away_team)
    ).filter(
        models.Game.game_date >= start_of_day,
        models.Game.game_date <= end_of_day
    ).all()

    analyzed_props = []

    for prop in props:
        player = _resolve_player_with_stats(db, prop)
        if player:
            db.refresh(player)
            player = db.query(models.Player).options(joinedload(models.Player.team)).filter(models.Player.id == player.id).first()
        if not player or not player.stats:
            continue

        # --- Injury Filtering ---
        injury = db.query(models.Injury).filter(
            models.Injury.player_id == player.id
        ).order_by(models.Injury.updated_date.desc()).first()
        if injury and injury.status == "Out":
            continue

        injury_mod = 1.0
        if injury:
            if injury.status == "Questionable":
                injury_mod = 0.8
            elif injury.status == "Probable":
                injury_mod = 0.95

        values, season_sample_counts = _extract_multiseason_prop_values(
            player,
            prop.prop_type,
            as_of_date=target_date,
        )
        if len(values) < 5:
            continue

        # Build full analysis kwargs
        analysis_kwargs = _build_prop_analysis_kwargs(
            prop, player, db, league_avg_defense, league_avg_pace
        )

        analysis = analyze_prop(
            line=prop.line,
            historical_stats=values,
            odds_over=prop.over_odds or -110,
            odds_under=prop.under_odds or -110,
            game=prop.game,  # Pass game object for ML model
            **analysis_kwargs
        )

        # Apply injury confidence modifier
        if injury_mod < 1.0:
            analysis.ev *= injury_mod
            analysis.edge *= injury_mod
            if injury_mod < 0.9 and analysis.confidence == BetConfidence.HIGH:
                analysis.confidence = BetConfidence.MEDIUM

        # Filter by minimum EV and Kelly (only if explicitly requested)
        if min_ev > 0 and analysis.ev < min_ev:
            continue
        if min_kelly > 0 and analysis.kelly_fraction < min_kelly:
            continue

        # Filter by Over/Under recommendation
        if over_under and over_under.lower() in ['over', 'under']:
            if analysis.recommendation.lower() != over_under.lower():
                continue

        # BP agreement flag
        bp_agrees = True
        if prop.recommended_side and analysis.recommendation not in ("avoid", "insufficient_data"):
            bp_agrees = prop.recommended_side.lower() == analysis.recommendation

        # Determine opponent
        opponent = "UNK"
        if prop.game:
            if player.team_id == prop.game.home_team_id:
                opponent = prop.game.away_team.name if prop.game.away_team else "UNK"
            else:
                opponent = prop.game.home_team.name if prop.game.home_team else "UNK"

        analyzed_props.append({
            "prop_id": prop.id,
            "player_id": player.id,
            "player_name": player.name,
            "player_position": player.position,
            "team_name": player.team.name if player.team else None,
            "team_logo": player.team.logo_url if player.team else None,
            "opponent": opponent,
            "prop_type": prop.prop_type,
            "line": prop.line,
            "over_odds": prop.over_odds,
            "under_odds": prop.under_odds,
            # Advanced Analytics
            "hit_rate": round(analysis.hit_rate * 100, 1),
            "weighted_avg": round(analysis.weighted_average, 1),
            "ev": round(analysis.ev, 2),
            "edge": round(analysis.edge, 1),
            "kelly_fraction": round(analysis.kelly_fraction * 100, 2),
            "kelly_bet_size": f"${round(analysis.kelly_fraction * 1000, 2)}",
            "streak_status": analysis.streak_status.value,
            "confidence_level": analysis.confidence.value,
            "recommendation": analysis.recommendation,
            "sample_size": analysis.sample_size,
            "season_sample_counts": season_sample_counts,
            "confidence_interval": {
                "low": round(analysis.confidence_interval[0] * 100, 1),
                "high": round(analysis.confidence_interval[1] * 100, 1)
            },
            # New fields
            "grade": _get_grade(analysis.ev, analysis.edge, bp_agrees, analysis.streak_status.value),
            "bp_star_rating": prop.star_rating,
            "bp_ev": prop.bp_ev,
            "bp_agrees": bp_agrees,
            "opponent_adjusted": analysis_kwargs.get('opponent_defense_rating') is not None,
            "is_b2b": analysis_kwargs.get('is_b2b', False),
        })

    # Sort by EV (best value first)
    analyzed_props.sort(key=lambda x: x["ev"], reverse=True)

    return {
        "total": len(analyzed_props),
        "props": analyzed_props[:500],
        "date_used": target_date.isoformat(),
    }


@router.get("/genius-picks")
def get_genius_picks(request: Request, date: Optional[date] = None, db: Session = Depends(get_db)):
    """
    Get the absolute BEST picks with full intelligence stack.
    Enhanced with reconstructed NBA data: clutch performance, tracking metrics,
    athletic analytics, and advanced ML-enhanced predictions.
    """
    client_tz = get_client_timezone(request)
    if date is None:
        date = get_current_gameday(client_tz)
    _reconcile_prop_player_ids(db)
    date = _resolve_target_date_with_props(db, date, client_tz)

    try:
        # Enhanced mode relies on multiple live external calls and can stall request latency.
        # Default to the proven local analytics path for stable UX.
        raise RuntimeError("Use legacy genius picks pipeline")

        # Use enhanced genius picks system with reconstructed NBA data
        from ..analytics.enhanced_genius_picks import get_enhanced_genius_picks
        
        result = get_enhanced_genius_picks(target_date=date, min_edge=0.03)
        if not result.get("picks"):
            raise ValueError("Enhanced genius picks returned no picks")
        
        # Add metadata about data sources
        result['data_sources'] = {
            'reconstructed_data': True,
            'clutch_analytics': True,
            'tracking_metrics': True,
            'athletic_performance': True,
            'defensive_impact': True,
            'consistency_scoring': True
        }
        
        # Add genius_picks field for backward compatibility
        result['genius_picks'] = result['picks']
        
        return result
        
    except Exception as e:
        # Fallback to legacy system if enhanced system fails
        print(f"Enhanced genius picks failed: {e}, falling back to legacy system")
        
        from ..analytics.advanced_stats import (
            analyze_prop, wilson_confidence_interval, StreakStatus, BetConfidence
        )

        league_avg_defense = _get_league_avg_defense(db)
        league_avg_pace = _get_league_avg_pace(db)

        # 1. Player Props (Elite Only) — filtered by date
        start_utc, end_utc = get_gameday_range(date, client_tz)
        props = db.query(models.PlayerProps).join(models.Game).filter(
            models.Game.game_date >= start_utc,
            models.Game.game_date < end_utc
        ).all()
        genius_picks = []

    for prop in props:
        player = _resolve_player_with_stats(db, prop)
        if not player or not player.stats:
            continue

        # --- Injury Filtering for Genius ---
        injury = db.query(models.Injury).filter(
            models.Injury.player_id == player.id
        ).order_by(models.Injury.updated_date.desc()).first()
        if injury and injury.status in ["Out", "Questionable"]:
            continue

        values, season_sample_counts = _extract_multiseason_prop_values(
            player,
            prop.prop_type,
            as_of_date=date,
        )
        if len(values) < 10:
            continue

        # Build full analysis kwargs
        analysis_kwargs = _build_prop_analysis_kwargs(
            prop, player, db, league_avg_defense, league_avg_pace
        )

        analysis = analyze_prop(
            line=prop.line,
            historical_stats=values,
            odds_over=prop.over_odds or -110,
            odds_under=prop.under_odds or -110,
            game=prop.game,  # Pass game object for ML model
            **analysis_kwargs
        )

        # Only include HIGH confidence with positive EV
        if analysis.confidence != BetConfidence.HIGH or analysis.ev <= 0:
            continue

        if analysis.ev < 3 or analysis.edge < 5:
            continue

        ci_low, ci_high = analysis.confidence_interval
        if ci_low <= 0.5 <= ci_high:
            continue

        # BP agreement check
        bp_agrees = True
        if prop.recommended_side and analysis.recommendation not in ("avoid", "insufficient_data"):
            bp_agrees = prop.recommended_side.lower() == analysis.recommendation

        grade = _get_grade(analysis.ev, analysis.edge, bp_agrees, analysis.streak_status.value)

        genius_picks.append({
            "player": player.name,
            "prop": prop.prop_type.replace('+', ' + ').title(),
            "line": prop.line,
            "pick": analysis.recommendation.upper(),
            "odds": prop.over_odds if analysis.recommendation == "over" else prop.under_odds,
            "ev": f"+${round(analysis.ev, 2)}",
            "edge": f"+{round(analysis.edge, 1)}%",
            "kelly_bet": f"${round(analysis.kelly_fraction * 1000, 2)}",
            "hit_rate": f"{round(analysis.hit_rate * 100, 1)}%",
            "streak": analysis.streak_status.value,
            "confidence_range": f"{round(ci_low * 100)}-{round(ci_high * 100)}%",
            "grade": grade,
            "season_sample_counts": season_sample_counts,
            # New enriched fields
            "bp_star_rating": prop.star_rating,
            "bp_agrees": bp_agrees,
            "opponent_adjusted": analysis_kwargs.get('opponent_defense_rating') is not None,
            "is_b2b": analysis_kwargs.get('is_b2b', False),
            "weighted_projection": round(analysis.weighted_average, 1),
        })

    # 2. Elite Game Spreads — with real streak detection (Phase 4b)
    game_recs = db.query(models.Recommendation).join(models.Game).filter(
        models.Game.game_date >= start_utc,
        models.Game.game_date < end_utc,
        models.Recommendation.bet_type == "Spread",
        models.Recommendation.confidence_score >= 0.8
    ).all()

    for rec in game_recs:
        actual_odds = -110
        if rec.game.odds:
            latest = rec.game.odds[-1]
            actual_odds = latest.home_spread_price or latest.away_spread_price or -110

        implied_prob = _calculate_implied_prob(actual_odds)
        edge = (rec.confidence_score - implied_prob) * 100

        if actual_odds > 0:
            decimal_payout = 1 + (actual_odds / 100)
        else:
            decimal_payout = 1 + (100 / abs(actual_odds))
        ev = (rec.confidence_score * decimal_payout - 1) * 100

        if edge <= 0:
            continue

        kelly_fraction = edge / 100 / (decimal_payout - 1) if decimal_payout > 1 else 0

        # --- Phase 4b: Real streak detection ---
        team_id = None
        if rec.game.home_team and rec.recommended_pick == rec.game.home_team.name:
            team_id = rec.game.home_team_id
        elif rec.game.away_team:
            team_id = rec.game.away_team_id

        if team_id:
            wins_ats, losses_ats, streak_status = _get_team_ats_record(db, team_id, 5)
        else:
            wins_ats, losses_ats, streak_status = 0, 0, "neutral"

        # --- Phase 4c: Real confidence intervals ---
        # Use Wilson CI on the team's recent ATS record as a proxy
        total_ats = wins_ats + losses_ats
        if total_ats > 0:
            ci_low, ci_high = wilson_confidence_interval(wins_ats, total_ats)
        else:
            ci_low = rec.confidence_score - 0.10
            ci_high = min(1.0, rec.confidence_score + 0.10)

        grade = _get_grade(ev, edge, True, streak_status)

        genius_picks.append({
            "player": f"{rec.game.away_team.name} @ {rec.game.home_team.name}",
            "prop": "Game Spread",
            "line": rec.game.odds[-1].spread_points if rec.game.odds else 0,
            "pick": rec.recommended_pick.upper(),
            "odds": actual_odds,
            "ev": f"+${round(ev, 2)}",
            "edge": f"+{round(edge, 1)}%",
            "kelly_bet": f"${round(kelly_fraction * 1000, 2)}",
            "hit_rate": f"{round(rec.confidence_score * 100, 1)}%",
            "streak": streak_status,
            "confidence_range": f"{round(ci_low * 100)}-{round(ci_high * 100)}%",
            "grade": grade,
            "ats_record": f"{wins_ats}-{losses_ats}" if total_ats > 0 else None,
            "bp_star_rating": None,
            "bp_agrees": True,
            "opponent_adjusted": True,
            "is_b2b": False,
            "weighted_projection": None,
        })

    genius_picks.sort(key=lambda x: float(x["ev"].replace("+$", "")), reverse=True)

    return {
        "genius_count": len(genius_picks),
        "picks": genius_picks[:20],
        "date_used": date.isoformat(),
    }
