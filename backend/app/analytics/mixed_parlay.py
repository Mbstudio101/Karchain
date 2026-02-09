"""
Enhanced Parlay Generator - Mixes Player Props with Game Bets
Uses statistical analysis to find the best value bets.
"""
import sys
sys.path.insert(0, '/Users/marvens/Desktop/Karchain/backend')

from app.database import SessionLocal
from app import models
from datetime import datetime
from typing import List, Tuple
import random

def calculate_prop_hit_rate(player: models.Player, prop_type: str, line: float) -> float:
    """Calculate historical hit rate for a prop."""
    if not player.stats:
        return 0.5
    
    stats = player.stats[:15]  # Last 15 games
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
    """Calculate expected value edge for a bet."""
    if odds > 0:
        decimal_odds = 1 + (odds / 100)
    else:
        decimal_odds = 1 + (100 / abs(odds))
    
    implied_prob = 1 / decimal_odds
    edge = probability - implied_prob
    return edge

def get_best_prop_bets(db, limit: int = 10) -> List[Tuple]:
    """Get player props with the highest edge based on historical performance."""
    best_bets = []
    
    props = db.query(models.PlayerProps).all()
    
    for prop in props:
        player = db.query(models.Player).filter(models.Player.id == prop.player_id).first()
        if not player or not player.stats or len(player.stats) < 5:
            continue
        
        hit_rate = calculate_prop_hit_rate(player, prop.prop_type, prop.line)
        
        # Calculate edge for over
        over_edge = calculate_edge(prop.over_odds, hit_rate)
        
        # Calculate edge for under
        under_edge = calculate_edge(prop.under_odds, 1 - hit_rate)
        
        if over_edge > 0.05:  # 5%+ edge on over
            best_bets.append({
                'type': 'prop',
                'player': player.name,
                'prop_type': prop.prop_type,
                'pick': 'OVER',
                'line': prop.line,
                'odds': prop.over_odds,
                'hit_rate': hit_rate,
                'edge': over_edge,
                'reasoning': f"{player.name} hits {prop.prop_type} over {prop.line} in {hit_rate*100:.0f}% of games"
            })
        
        if under_edge > 0.05:  # 5%+ edge on under
            best_bets.append({
                'type': 'prop',
                'player': player.name,
                'prop_type': prop.prop_type,
                'pick': 'UNDER',
                'line': prop.line,
                'odds': prop.under_odds,
                'hit_rate': 1 - hit_rate,
                'edge': under_edge,
                'reasoning': f"{player.name} stays under {prop.line} {prop.prop_type} in {(1-hit_rate)*100:.0f}% of games"
            })
    
    # Sort by edge and return top bets
    best_bets.sort(key=lambda x: x['edge'], reverse=True)
    return best_bets[:limit]

def get_best_game_bets(db, limit: int = 5) -> List[Tuple]:
    """Get game spreads/moneylines with value."""
    best_bets = []
    
    recommendations = db.query(models.Recommendation).order_by(
        models.Recommendation.confidence_score.desc()
    ).limit(limit).all()
    
    for rec in recommendations:
        game = db.query(models.Game).filter(models.Game.id == rec.game_id).first()
        if not game or not game.odds:
            continue
        
        latest_odds = game.odds[-1]
        
        if 'spread' in rec.bet_type.lower():
            odds = latest_odds.home_spread_price if rec.recommended_pick == game.home_team.name else latest_odds.away_spread_price
            line = abs(latest_odds.spread_points)
        else:
            odds = latest_odds.home_moneyline if rec.recommended_pick == game.home_team.name else latest_odds.away_moneyline
            line = None
        
        if odds is None:
            odds = -110
        
        best_bets.append({
            'type': 'game',
            'game': f"{game.away_team.name} @ {game.home_team.name}",
            'bet_type': rec.bet_type,
            'pick': rec.recommended_pick,
            'line': line,
            'odds': odds,
            'confidence': rec.confidence_score,
            'edge': rec.confidence_score - 0.5,  # Simple edge calculation
            'reasoning': rec.reasoning or f"AI pick: {rec.recommended_pick}"
        })
    
    return best_bets

def generate_mixed_parlay(legs: int = 5):
    """Generate an optimized parlay mixing player props and game bets."""
    db = SessionLocal()
    
    try:
        # Get best bets from both sources
        prop_bets = get_best_prop_bets(db, limit=20)
        game_bets = get_best_game_bets(db, limit=10)
        
        # Combine and select optimal mix
        # Strategy: ~60% props, ~40% game bets for diversification
        num_props = int(legs * 0.6)
        num_games = legs - num_props
        
        selected = []
        
        # Add top prop bets
        for bet in prop_bets[:num_props]:
            selected.append(bet)
        
        # Add top game bets
        for bet in game_bets[:num_games]:
            selected.append(bet)
        
        # If not enough, fill with whatever we have
        remaining = legs - len(selected)
        all_bets = prop_bets + game_bets
        for bet in all_bets:
            if bet not in selected and remaining > 0:
                selected.append(bet)
                remaining -= 1
        
        # Calculate combined odds
        combined_decimal = 1.0
        for bet in selected:
            odds = bet['odds']
            if odds > 0:
                decimal_odds = 1 + (odds / 100)
            else:
                decimal_odds = 1 + (100 / abs(odds))
            combined_decimal *= decimal_odds
        
        if combined_decimal >= 2:
            combined_american = int((combined_decimal - 1) * 100)
        else:
            combined_american = int(-100 / (combined_decimal - 1))
        
        payout = 100 * combined_decimal
        avg_edge = sum(b.get('edge', 0) for b in selected) / len(selected) if selected else 0
        
        print("\n" + "="*60)
        print("🎯 OPTIMIZED MIXED PARLAY")
        print("="*60)
        
        for i, bet in enumerate(selected, 1):
            if bet['type'] == 'prop':
                print(f"\n[Leg {i}] PLAYER PROP")
                print(f"  {bet['player']} - {bet['prop_type'].upper()} {bet['pick']} {bet['line']}")
                print(f"  Odds: {bet['odds']:+d} | Hit Rate: {bet['hit_rate']*100:.0f}%")
            else:
                print(f"\n[Leg {i}] GAME BET")
                print(f"  {bet['game']}")
                print(f"  {bet['bet_type']}: {bet['pick']}")
                print(f"  Odds: {bet['odds']:+d}")
            print(f"  Edge: {bet['edge']*100:.1f}%")
        
        print("\n" + "-"*60)
        print(f"Combined Odds: {combined_american:+d}")
        print(f"Potential Payout ($100): ${payout:.2f}")
        print(f"Average Edge: {avg_edge*100:.1f}%")
        print("="*60 + "\n")
        
        return {
            'legs': selected,
            'combined_odds': combined_american,
            'payout': payout,
            'avg_edge': avg_edge
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_mixed_parlay(5)
