from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from .. import models, schemas
from ..dependencies import get_db
from ..date_utils import get_current_gameday

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)

@router.get("/", response_model=List[schemas.RecommendationBase])
def get_recommendations(date: Optional[date] = None, db: Session = Depends(get_db)):
    """
    Returns recommendations. Defaults to today's games if no date provided.
    """
    if date is None:
        date = get_current_gameday()
        
    # Join with Game to filter by game_date
    recs = db.query(models.Recommendation).join(models.Game).filter(
        models.Game.game_date >= datetime.combine(date, datetime.min.time()),
        models.Game.game_date <= datetime.combine(date, datetime.max.time())
    ).order_by(models.Recommendation.confidence_score.desc()).all()
    
    return recs

@router.post("/generate", response_model=List[schemas.RecommendationBase])
def generate_recommendations(db: Session = Depends(get_db)):
    """
    Generates recommendations for ACTIVE or UPCOMING games only.
    """
    # Only analyze games that aren't Final
    games = db.query(models.Game).filter(models.Game.status.in_(["Scheduled", "Live"])).all()
    generated_recs = []
    
    # --- Helper Functions ---
    def calculate_implied_prob(american_odds: int) -> float:
        """Converts American odds to implied probability (0.0 - 1.0)."""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)

    def calculate_pythagorean_win_pct(ppg: float, opp_ppg: float, exponent: float = 13.91) -> float:
        """
        Calculates expected win percentage using Bill James' Pythagorean Expectation.
        Exponent 13.91 is standard for NBA.
        """
        if ppg == 0 and opp_ppg == 0:
            return 0.5
        return (ppg ** exponent) / ((ppg ** exponent) + (opp_ppg ** exponent))

    for game in games:
        # 1. Skip if game involves teams without stats
        if not game.home_team.stats or not game.away_team.stats:
            continue
            
        home_stats = game.home_team.stats[0] # Assuming latest season stats are first/relevant
        away_stats = game.away_team.stats[0]
        
        # 2. Get latest odds
        if not game.odds:
            continue
            
        latest_odds = game.odds[-1]
        
        # --- Moneyline Analysis ---
        if latest_odds.home_moneyline and latest_odds.away_moneyline:
            # Calculate True Probabilities
            home_win_prob = calculate_pythagorean_win_pct(home_stats.ppg, home_stats.opp_ppg)
            away_win_prob = calculate_pythagorean_win_pct(away_stats.ppg, away_stats.opp_ppg)
            
            # Adjust for Home Court Advantage (approx +3-4% in NBA)
            home_win_prob += 0.035
            away_win_prob -= 0.035
            
            # Calculate Implied Probabilities
            home_implied = calculate_implied_prob(latest_odds.home_moneyline)
            away_implied = calculate_implied_prob(latest_odds.away_moneyline)
            
            # Check for Value (Edge > 5%)
            if home_win_prob > home_implied + 0.05:
                edge = home_win_prob - home_implied
                _create_rec(db, generated_recs, game, "Moneyline", game.home_team.name, edge, 
                           f"High Value: Model gives {home_win_prob:.1%} chance vs Vegas {home_implied:.1%}. Edge: {edge:.1%}")
                           
            elif away_win_prob > away_implied + 0.05:
                edge = away_win_prob - away_implied
                _create_rec(db, generated_recs, game, "Moneyline", game.away_team.name, edge, 
                           f"Upset Alert: Model gives {away_win_prob:.1%} chance vs Vegas {away_implied:.1%}. Edge: {edge:.1%}")

        # --- Spread Analysis ---
        if latest_odds.spread_points:
            # Estimate Expected Spread based on Net Rating difference
            # Simple approximation: (Home Net Rating - Away Net Rating) + Home Court (3 pts)
            home_net = home_stats.ppg - home_stats.opp_ppg
            away_net = away_stats.ppg - away_stats.opp_ppg
            
            expected_spread_margin = (home_net - away_net) + 3.0
            # Note: A positive margin means Home wins by X. 
            # Vegas spreads are usually negative for favorites (e.g. -5.5). 
            # So if Expected is +7.0, fair spread is -7.0.
            
            fair_spread_line = -1 * expected_spread_margin
            vegas_spread = latest_odds.spread_points
            
            diff = fair_spread_line - vegas_spread
            
            # If Diff is > 3 points, we have an edge
            if abs(diff) > 3.0:
                if diff < 0: 
                    # Fair spread is closer to -10 than -5. Home team is stronger than Vegas thinks.
                    pick = game.home_team.name
                    # Margin of edge (diff) determines confidence
                    # e.g. 3 point diff = ~65%, 7 point diff = ~85%
                    confidence = min(0.98, 0.5 + (abs(diff) / 20))
                    reason = f"Simulated Spread: {fair_spread_line:.1f} vs Vegas: {vegas_spread}. Home team significantly undervalued by {abs(diff):.1f} points."
                else:
                    # Fair spread is closer to +5 than -5. Away team is stronger/Home is weaker.
                    pick = game.away_team.name
                    confidence = min(0.98, 0.5 + (abs(diff) / 20))
                    reason = f"Simulated Spread: {fair_spread_line:.1f} vs Vegas: {vegas_spread}. Away team significantly undervalued by {abs(diff):.1f} points."
                
                _create_rec(db, generated_recs, game, "Spread", pick, confidence, reason)

    return generated_recs

def _create_rec(db, list_ref, game, bet_type, pick, confidence, reason):
    """Helper to check existence and add recommendation"""
    # Check if exists
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
    list_ref.append(rec)

@router.post("/generate-parlay", response_model=schemas.ParlayBase)
def generate_parlay(legs: int = 3, db: Session = Depends(get_db)):
    """
    Generate an AI-powered parlay by selecting the highest confidence bets.
    """
    # Get top recommendations sorted by confidence
    top_recs = db.query(models.Recommendation).order_by(
        models.Recommendation.confidence_score.desc()
    ).limit(legs).all()
    
    if len(top_recs) < legs:
        raise HTTPException(status_code=400, detail=f"Not enough recommendations to build a {legs}-leg parlay. Generate more first.")
    
    parlay_legs = []
    combined_decimal_odds = 1.0
    total_confidence = 0.0
    
    for rec in top_recs:
        # Get odds for the game
        game = db.query(models.Game).filter(models.Game.id == rec.game_id).first()
        if not game or not game.odds:
            continue
            
        latest_odds = game.odds[-1]
        
        # Determine which odds to use based on the pick
        if "spread" in rec.bet_type.lower():
            american_odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
        else:
            american_odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline
        
        if american_odds is None:
            american_odds = -110  # Default
        
        # Convert American odds to decimal for multiplication
        if american_odds > 0:
            decimal_odds = 1 + (american_odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(american_odds))
        
        combined_decimal_odds *= decimal_odds
        total_confidence += rec.confidence_score
        
        parlay_legs.append(schemas.ParlayLeg(
            game_id=rec.game_id,
            pick=rec.recommended_pick,
            odds=american_odds,
            confidence=rec.confidence_score
        ))
    
    # Convert combined decimal odds back to American
    if combined_decimal_odds >= 2:
        combined_american = int((combined_decimal_odds - 1) * 100)
    else:
        combined_american = int(-100 / (combined_decimal_odds - 1))
    
    # Calculate potential payout for $100
    potential_payout = 100 * combined_decimal_odds
    
    return schemas.ParlayBase(
        legs=parlay_legs,
        combined_odds=combined_american,
        potential_payout=round(potential_payout, 2),
        confidence_score=round(total_confidence / len(parlay_legs), 2) if parlay_legs else 0
    )

@router.post("/generate-mixed-parlay")
def generate_mixed_parlay(legs: int = 5, db: Session = Depends(get_db)):
    """
    Generate an AI-powered parlay mixing player props with game bets.
    Uses statistical analysis to find the best value bets.
    """
    from typing import List, Dict
    
    def calculate_prop_hit_rate(player, prop_type: str, line: float) -> float:
        """Calculate historical hit rate for a prop."""
        if not player.stats:
            return 0.5
        stats = player.stats[:15]
        hits = 0
        for stat in stats:
            if prop_type == 'points':
                value = stat.points or 0
            elif prop_type == 'rebounds':
                value = stat.rebounds or 0
            elif prop_type == 'assists':
                value = stat.assists or 0
            elif prop_type == 'pts+reb+ast':
                value = (stat.points or 0) + (stat.rebounds or 0) + (stat.assists or 0)
            else:
                value = 0
            if value > line:
                hits += 1
        return hits / len(stats) if stats else 0.5
    
    def calculate_edge(odds: int, probability: float) -> float:
        """Calculate expected value edge."""
        if odds > 0:
            decimal_odds = 1 + (odds / 100)
        else:
            decimal_odds = 1 + (100 / abs(odds))
        implied_prob = 1 / decimal_odds
        return probability - implied_prob
    
    # Get best prop bets
    prop_bets = []
    props = db.query(models.PlayerProps).all()
    
    for prop in props:
        player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
        if not player or not player.stats or len(player.stats) < 5:
            continue
        
        hit_rate = calculate_prop_hit_rate(player, prop.prop_type, prop.line)
        over_edge = calculate_edge(prop.over_odds, hit_rate)
        under_edge = calculate_edge(prop.under_odds, 1 - hit_rate)
        
        if over_edge > 0.03:
            prop_bets.append({
                'type': 'prop',
                'player_name': player.name,
                'prop_type': prop.prop_type,
                'pick': f"{player.name} {prop.prop_type.upper()} OVER {prop.line}",
                'odds': prop.over_odds,
                'confidence': min(0.95, 0.5 + over_edge),
                'edge': over_edge
            })
        
        if under_edge > 0.03:
            prop_bets.append({
                'type': 'prop',
                'player_name': player.name,
                'prop_type': prop.prop_type,
                'pick': f"{player.name} {prop.prop_type.upper()} UNDER {prop.line}",
                'odds': prop.under_odds,
                'confidence': min(0.95, 0.5 + under_edge),
                'edge': under_edge
            })
    
    # Get best game bets
    game_bets = []
    recommendations = db.query(models.Recommendation).order_by(
        models.Recommendation.confidence_score.desc()
    ).limit(10).all()
    
    for rec in recommendations:
        game = db.query(models.Game).filter(models.Game.id == rec.game_id).first()
        if not game or not game.odds:
            continue
        latest_odds = game.odds[-1]
        
        if "spread" in rec.bet_type.lower():
            odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
        else:
            odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline
        
        if odds is None:
            odds = -110
        
        game_bets.append({
            'type': 'game',
            'game_id': rec.game_id,
            'pick': f"{rec.recommended_pick} ({rec.bet_type})",
            'odds': odds,
            'confidence': rec.confidence_score,
            'edge': rec.confidence_score - 0.5
        })
    
    # Sort all bets by edge
    prop_bets.sort(key=lambda x: x['edge'], reverse=True)
    game_bets.sort(key=lambda x: x['edge'], reverse=True)
    
    # Mix: Target 50/50 split
    num_games_target = legs // 2
    num_props_target = legs - num_games_target
    
    selected_games = game_bets[:num_games_target]
    selected_props = prop_bets[:num_props_target]
    
    selected = selected_games + selected_props
    
    # Fill if needed from either pool
    all_remaining = [b for b in (game_bets + prop_bets) if b not in selected]
    all_remaining.sort(key=lambda x: x['edge'], reverse=True)
    
    while len(selected) < legs and all_remaining:
        selected.append(all_remaining.pop(0))
    
    if len(selected) < legs:
        raise HTTPException(status_code=400, detail=f"Not enough high-quality bets available. Found {len(selected)}, need {legs}.")
    
    # Build parlay
    parlay_legs = []
    combined_decimal = 1.0
    total_confidence = 0.0
    
    for bet in selected[:legs]:
        odds = bet['odds']
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
            confidence=bet['confidence']
        ))
    
    if combined_decimal >= 2:
        combined_american = int((combined_decimal - 1) * 100)
    else:
        combined_american = int(-100 / (combined_decimal - 1))
    
    potential_payout = 100 * combined_decimal
    
    return schemas.ParlayBase(
        legs=parlay_legs,
        combined_odds=combined_american,
        potential_payout=round(potential_payout, 2),
        confidence_score=round(total_confidence / len(parlay_legs), 2)
    )

@router.get("/advanced-props")
def get_advanced_props(min_ev: float = 0, min_kelly: float = 0, db: Session = Depends(get_db)):
    """
    Get player props with advanced analytics including:
    - Kelly Criterion optimal bet sizing
    - Expected Value (EV) calculation
    - Hot/Cold streak detection
    - Weighted recency analysis
    - Confidence intervals
    """
    from ..analytics.advanced_stats import (
        analyze_prop, kelly_criterion, calculate_ev, detect_streak,
        weighted_average, recency_hit_rate, wilson_confidence_interval,
        StreakStatus, BetConfidence
    )
    
    # Get all props with player stats
    props = db.query(models.PlayerProps).all()
    
    analyzed_props = []
    
    for prop in props:
        player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
        if not player or not player.stats:
            continue
        
        # Extract historical stat values
        stats_list = player.stats[:20]  # Last 20 games
        if not stats_list:
            continue
        
        # Get stat values based on prop type
        if prop.prop_type == 'points':
            values = [s.points or 0 for s in stats_list if s.points is not None]
        elif prop.prop_type == 'rebounds':
            values = [s.rebounds or 0 for s in stats_list if s.rebounds is not None]
        elif prop.prop_type == 'assists':
            values = [s.assists or 0 for s in stats_list if s.assists is not None]
        elif prop.prop_type == 'pts+reb+ast':
            values = [(s.points or 0) + (s.rebounds or 0) + (s.assists or 0) for s in stats_list]
        else:
            values = []
        
        if len(values) < 5:
            continue
        
        # Perform advanced analysis
        analysis = analyze_prop(
            line=prop.line,
            historical_stats=values,
            odds_over=prop.over_odds or -110,
            odds_under=prop.under_odds or -110
        )
        
        # Filter by minimum EV and Kelly
        if analysis.ev < min_ev or analysis.kelly_fraction < min_kelly:
            continue
        
        analyzed_props.append({
            "prop_id": prop.id,
            "player_id": player.id,
            "player_name": player.name,
            "player_position": player.position,
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
            "kelly_bet_size": f"${round(analysis.kelly_fraction * 1000, 2)}",  # For $1000 bankroll
            "streak_status": analysis.streak_status.value,
            "confidence_level": analysis.confidence.value,
            "recommendation": analysis.recommendation,
            "sample_size": analysis.sample_size,
            "confidence_interval": {
                "low": round(analysis.confidence_interval[0] * 100, 1),
                "high": round(analysis.confidence_interval[1] * 100, 1)
            }
        })
    
    # Sort by EV (best value first)
    analyzed_props.sort(key=lambda x: x["ev"], reverse=True)
    
    return {
        "total": len(analyzed_props),
        "props": analyzed_props[:100]  # Top 100
    }


@router.get("/genius-picks")
def get_genius_picks(date: Optional[date] = None, db: Session = Depends(get_db)):
    """
    Get the absolute BEST picks. Defaults to today.
    Only returns HIGH confidence bets with positive EV.
    """
    if date is None:
        date = get_current_gameday()
        
    from ..analytics.advanced_stats import (
        analyze_prop, StreakStatus, BetConfidence
    )
    
    # 1. Start with Player Props (Elite Only)
    props = db.query(models.PlayerProps).join(models.Game).filter(
        models.Game.game_date >= datetime.combine(date, datetime.min.time()),
        models.Game.game_date <= datetime.combine(date, datetime.max.time())
    ).all()
    genius_picks = []
    
    # helper for grade
    def get_grade(ev, edge):
        if ev > 5 and edge > 8: return "A+"
        return "A"
    
    for prop in props:
        player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
        if not player or not player.stats:
            continue
        
        stats_list = player.stats[:20]
        if len(stats_list) < 10:  # Require minimum 10 games for genius picks
            continue
        
        # Get stat values
        if prop.prop_type == 'points':
            values = [s.points or 0 for s in stats_list if s.points is not None]
        elif prop.prop_type == 'rebounds':
            values = [s.rebounds or 0 for s in stats_list if s.rebounds is not None]
        elif prop.prop_type == 'assists':
            values = [s.assists or 0 for s in stats_list if s.assists is not None]
        elif prop.prop_type == 'pts+reb+ast':
            values = [(s.points or 0) + (s.rebounds or 0) + (s.assists or 0) for s in stats_list]
        else:
            continue
        
        if len(values) < 10:
            continue
        
        analysis = analyze_prop(
            line=prop.line,
            historical_stats=values,
            odds_over=prop.over_odds or -110,
            odds_under=prop.under_odds or -110
        )
        
        # Only include HIGH confidence with positive EV
        if analysis.confidence != BetConfidence.HIGH or analysis.ev <= 0:
            continue
        
        # Genius tier requires:
        # - EV > $3 per $100 bet
        # - Edge > 5%
        # - Hit rate confidence interval doesn't include 50%
        if analysis.ev < 3 or analysis.edge < 5:
            continue
        
        ci_low, ci_high = analysis.confidence_interval
        if ci_low <= 0.5 <= ci_high:
            continue  # Skip if 50% is in confidence interval
        
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
            "grade": get_grade(analysis.ev, analysis.edge)
        })
    
    # 2. Add Elite Game Spreads
    game_recs = db.query(models.Recommendation).join(models.Game).filter(
        models.Game.game_date >= datetime.combine(date, datetime.min.time()),
        models.Game.game_date <= datetime.combine(date, datetime.max.time()),
        models.Recommendation.bet_type == "Spread",
        models.Recommendation.confidence_score >= 0.8  # Elite confidence
    ).all()
    
    for rec in game_recs:
        # Convert Confidence to EV-like grade
        # confidence 0.8 -> ~5-7% edge
        edge = (rec.confidence_score - 0.5) * 20 # Approximation
        ev = edge * 0.8 # Approximation
        
        genius_picks.append({
            "player": f"{rec.game.away_team.name} @ {rec.game.home_team.name}",
            "prop": "Game Spread",
            "line": rec.game.odds[-1].spread_points if rec.game.odds else 0,
            "pick": rec.recommended_pick.upper(),
            "odds": -110,
            "ev": f"+${round(ev, 2)}",
            "edge": f"+{round(edge, 1)}%",
            "kelly_bet": f"${round(edge/10 * 100, 2)}",
            "hit_rate": f"{round(rec.confidence_score * 100, 1)}%",
            "streak": "hot" if rec.confidence_score > 0.85 else "neutral",
            "confidence_range": f"{round(rec.confidence_score*100-5)}-{round(rec.confidence_score*100+5)}%",
            "grade": get_grade(ev, edge)
        })

    genius_picks.sort(key=lambda x: float(x["ev"].replace("+$", "")), reverse=True)
    
    return {
        "genius_count": len(genius_picks),
        "picks": genius_picks[:20]  # Top 20 genius picks
    }
