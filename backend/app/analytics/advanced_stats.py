"""
Advanced Statistics Module for Karchain
Professional-grade analytics for sports betting predictions.
"""
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum
import math

class StreakStatus(Enum):
    HOT = "hot"
    COLD = "cold"
    NEUTRAL = "neutral"

class BetConfidence(Enum):
    HIGH = "high"       # 70%+ probability
    MEDIUM = "medium"   # 55-70% probability
    LOW = "low"         # Below 55%
    AVOID = "avoid"     # Negative EV

@dataclass
class PropAnalysis:
    """Complete analysis for a player prop."""
    hit_rate: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    edge: float
    ev: float
    kelly_fraction: float
    streak_status: StreakStatus
    weighted_average: float
    recommendation: str
    confidence: BetConfidence

# =============================================================================
# KELLY CRITERION
# =============================================================================

def kelly_criterion(probability: float, odds: int) -> float:
    """
    Calculate optimal bet size as fraction of bankroll using Kelly Criterion.
    
    Args:
        probability: Estimated win probability (0-1)
        odds: American odds format
        
    Returns:
        Optimal bet size as fraction of bankroll (0-1)
        Returns 0 if negative edge (don't bet)
    """
    if probability <= 0 or probability >= 1:
        return 0.0
    
    # Convert American odds to decimal
    if odds > 0:
        decimal = 1 + (odds / 100)
    else:
        decimal = 1 + (100 / abs(odds))
    
    b = decimal - 1  # Net odds (profit per $1 bet)
    q = 1 - probability
    
    # Kelly formula: f* = (bp - q) / b
    kelly = (b * probability - q) / b
    
    # Use fractional Kelly (half) for safety
    # Never bet more than 5% of bankroll
    half_kelly = kelly * 0.5
    return max(0, min(half_kelly, 0.05))


def kelly_with_confidence(probability: float, odds: int, confidence: float) -> float:
    """
    Kelly Criterion adjusted by confidence in the probability estimate.
    
    Args:
        probability: Estimated win probability
        odds: American odds
        confidence: How confident are you in the probability (0-1)
    """
    base_kelly = kelly_criterion(probability, odds)
    # Scale Kelly by confidence
    return base_kelly * confidence

# =============================================================================
# EXPECTED VALUE
# =============================================================================

def calculate_ev(probability: float, odds: int, stake: float = 100) -> float:
    """
    Calculate Expected Value of a bet.
    
    Args:
        probability: Estimated win probability (0-1)
        odds: American odds
        stake: Amount wagered
        
    Returns:
        Expected value (+/- amount per bet)
    """
    # Calculate potential profit
    if odds > 0:
        profit = stake * (odds / 100)
    else:
        profit = stake * (100 / abs(odds))
    
    # EV = (P(win) × Profit) - (P(lose) × Stake)
    ev = (probability * profit) - ((1 - probability) * stake)
    return ev


def ev_percentage(probability: float, odds: int) -> float:
    """
    Calculate EV as a percentage of stake.
    
    Returns:
        Percentage edge (e.g., 5.2 means +5.2% edge)
    """
    ev = calculate_ev(probability, odds, stake=100)
    return ev  # Already a percentage of the $100 stake

# =============================================================================
# STREAK DETECTION
# =============================================================================

def detect_streak(stats: List[float], window: int = 5, threshold: float = 0.15) -> StreakStatus:
    """
    Detect if player is on a hot or cold streak.
    
    Args:
        stats: List of recent stat values (most recent last)
        window: Number of recent games to consider
        threshold: Deviation threshold to trigger hot/cold (15% default)
        
    Returns:
        StreakStatus enum
    """
    if len(stats) < window:
        return StreakStatus.NEUTRAL
    
    recent_avg = sum(stats[-window:]) / window
    season_avg = sum(stats) / len(stats)
    
    if season_avg == 0:
        return StreakStatus.NEUTRAL
    
    deviation = (recent_avg - season_avg) / season_avg
    
    if deviation > threshold:
        return StreakStatus.HOT
    elif deviation < -threshold:
        return StreakStatus.COLD
    return StreakStatus.NEUTRAL


def streak_modifier(status: StreakStatus) -> float:
    """
    Get probability modifier based on streak status.
    Hot players get slight probability boost, cold players get reduction.
    """
    modifiers = {
        StreakStatus.HOT: 1.05,      # +5% boost
        StreakStatus.NEUTRAL: 1.0,   # No change
        StreakStatus.COLD: 0.95      # -5% reduction
    }
    return modifiers[status]

# =============================================================================
# WEIGHTED RECENCY
# =============================================================================

def weighted_average(stats: List[float], decay: float = 0.85) -> float:
    """
    Calculate weighted average where recent games matter more.
    
    Args:
        stats: List of stat values (most recent last)
        decay: Weight decay factor (0.85 = each older game worth 15% less)
        
    Returns:
        Weighted average value
    """
    if not stats:
        return 0.0
    
    # Reverse so most recent is first
    reversed_stats = stats[::-1]
    
    weights = [decay ** i for i in range(len(reversed_stats))]
    weighted_sum = sum(s * w for s, w in zip(reversed_stats, weights))
    total_weight = sum(weights)
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def recency_hit_rate(line: float, stats: List[float], decay: float = 0.85) -> float:
    """
    Calculate hit rate with recency weighting.
    More recent games contribute more to the hit rate.
    """
    if not stats:
        return 0.5
    
    reversed_stats = stats[::-1]
    weights = [decay ** i for i in range(len(reversed_stats))]
    
    weighted_hits = sum(w for s, w in zip(reversed_stats, weights) if s > line)
    total_weight = sum(weights)
    
    return weighted_hits / total_weight if total_weight > 0 else 0.5

# =============================================================================
# OPPONENT ADJUSTMENT
# =============================================================================

def opponent_adjusted_projection(
    player_avg: float,
    opponent_defense_rating: float,
    league_avg_defense: float = 100.0
) -> float:
    """
    Adjust player projection based on opponent defensive strength.
    
    Args:
        player_avg: Player's average for the stat
        opponent_defense_rating: Opponent's defensive rating (lower = better defense)
        league_avg_defense: League average defensive rating
        
    Returns:
        Adjusted projection
    """
    # Adjustment factor: opponent_defense / league_avg
    # If opponent allows more than average (higher rating), boost projection
    # If opponent allows less than average (lower rating), reduce projection
    adjustment = opponent_defense_rating / league_avg_defense
    return player_avg * adjustment


def pace_adjusted_projection(
    player_avg: float,
    opponent_pace: float,
    league_avg_pace: float = 100.0
) -> float:
    """
    Adjust projection based on opponent's pace of play.
    Faster pace = more possessions = more opportunities.
    """
    pace_factor = opponent_pace / league_avg_pace
    return player_avg * pace_factor

# =============================================================================
# CORRELATION DETECTION
# =============================================================================

@dataclass
class CorrelationRisk:
    level: str  # "high", "medium", "low", "none"
    reason: str
    penalty: float  # Odds multiplier penalty

def detect_correlation(bet1: Dict, bet2: Dict) -> CorrelationRisk:
    """
    Detect if two bets are correlated (reduces parlay value).
    
    High correlation: Same player, different props
    Medium correlation: Same game, related outcomes
    Low correlation: Different games, similar player types
    None: Truly independent bets
    """
    # Same player = high correlation
    if bet1.get("player_id") == bet2.get("player_id"):
        return CorrelationRisk(
            level="high",
            reason="Same player - props are highly correlated",
            penalty=0.85  # 15% odds penalty
        )
    
    # Same game = medium correlation
    if bet1.get("game_id") == bet2.get("game_id"):
        return CorrelationRisk(
            level="medium",
            reason="Same game - outcomes may be related",
            penalty=0.95  # 5% odds penalty
        )
    
    # Different games, same team = low correlation
    if bet1.get("team_id") == bet2.get("team_id"):
        return CorrelationRisk(
            level="low",
            reason="Same team - slight correlation possible",
            penalty=0.98
        )
    
    return CorrelationRisk(
        level="none",
        reason="Independent bets",
        penalty=1.0
    )


def calculate_parlay_correlation_penalty(bets: List[Dict]) -> float:
    """
    Calculate total correlation penalty for a parlay.
    Returns multiplier to apply to theoretical odds.
    """
    if len(bets) < 2:
        return 1.0
    
    total_penalty = 1.0
    
    for i, bet1 in enumerate(bets):
        for bet2 in bets[i+1:]:
            correlation = detect_correlation(bet1, bet2)
            total_penalty *= correlation.penalty
    
    return total_penalty

# =============================================================================
# CONFIDENCE INTERVALS
# =============================================================================

def wilson_confidence_interval(hits: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate Wilson score confidence interval for binomial proportion.
    More accurate than simple standard error for small samples.
    
    Args:
        hits: Number of successful outcomes
        total: Total number of trials
        confidence: Desired confidence level (default 95%)
        
    Returns:
        (lower_bound, upper_bound) tuple
    """
    if total == 0:
        return (0.0, 1.0)
    
    # Z-score for confidence level
    z = 1.96 if confidence == 0.95 else 1.645  # 95% or 90%
    
    p = hits / total
    
    denominator = 1 + z**2 / total
    center = (p + z**2 / (2 * total)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denominator
    
    return (max(0, center - spread), min(1, center + spread))


def sample_size_sufficient(total: int, min_samples: int = 10) -> bool:
    """Check if sample size is sufficient for reliable analysis."""
    return total >= min_samples

# =============================================================================
# COMBINED ANALYSIS
# =============================================================================

def analyze_prop(
    line: float,
    historical_stats: List[float],
    odds_over: int,
    odds_under: int,
    opponent_defense_rating: Optional[float] = None,
    league_avg_defense: float = 100.0
) -> PropAnalysis:
    """
    Perform complete analysis of a player prop.
    
    Returns comprehensive PropAnalysis with all metrics.
    """
    if not historical_stats:
        return PropAnalysis(
            hit_rate=0.5,
            confidence_interval=(0.0, 1.0),
            sample_size=0,
            edge=0.0,
            ev=0.0,
            kelly_fraction=0.0,
            streak_status=StreakStatus.NEUTRAL,
            weighted_average=0.0,
            recommendation="insufficient_data",
            confidence=BetConfidence.AVOID
        )
    
    # Basic hit rate
    hits = sum(1 for s in historical_stats if s > line)
    total = len(historical_stats)
    basic_hit_rate = hits / total if total > 0 else 0.5
    
    # Confidence interval
    ci = wilson_confidence_interval(hits, total)
    
    # Weighted hit rate (recency)
    weighted_hit = recency_hit_rate(line, historical_stats)
    
    # Streak detection
    streak = detect_streak(historical_stats)
    streak_mod = streak_modifier(streak)
    
    # Apply streak modifier
    adjusted_hit_rate = min(0.95, max(0.05, weighted_hit * streak_mod))
    
    # Opponent adjustment if available
    weighted_avg = weighted_average(historical_stats)
    if opponent_defense_rating:
        adjusted_projection = opponent_adjusted_projection(
            weighted_avg, opponent_defense_rating, league_avg_defense
        )
        # Re-estimate hit rate based on adjusted projection
        if adjusted_projection > line:
            adjusted_hit_rate = min(adjusted_hit_rate * 1.05, 0.95)
        else:
            adjusted_hit_rate = max(adjusted_hit_rate * 0.95, 0.05)
    
    # Calculate EV for both sides
    ev_over = calculate_ev(adjusted_hit_rate, odds_over)
    ev_under = calculate_ev(1 - adjusted_hit_rate, odds_under)
    
    # Determine best side
    if ev_over > ev_under and ev_over > 0:
        best_ev = ev_over
        best_odds = odds_over
        best_prob = adjusted_hit_rate
        recommendation = "over"
    elif ev_under > 0:
        best_ev = ev_under
        best_odds = odds_under
        best_prob = 1 - adjusted_hit_rate
        recommendation = "under"
    else:
        best_ev = max(ev_over, ev_under)
        best_odds = odds_over if ev_over > ev_under else odds_under
        best_prob = adjusted_hit_rate if ev_over > ev_under else 1 - adjusted_hit_rate
        recommendation = "avoid"
    
    # Kelly fraction
    kelly = kelly_criterion(best_prob, best_odds)
    
    # Edge calculation
    implied_prob = 100 / (100 + abs(best_odds)) if best_odds < 0 else 100 / (100 + best_odds)
    edge = (best_prob - implied_prob) * 100
    
    # Confidence level
    if best_ev > 5 and sample_size_sufficient(total, 15):
        confidence = BetConfidence.HIGH
    elif best_ev > 0 and sample_size_sufficient(total, 10):
        confidence = BetConfidence.MEDIUM
    elif best_ev > 0:
        confidence = BetConfidence.LOW
    else:
        confidence = BetConfidence.AVOID
    
    return PropAnalysis(
        hit_rate=basic_hit_rate,
        confidence_interval=ci,
        sample_size=total,
        edge=edge,
        ev=best_ev,
        kelly_fraction=kelly,
        streak_status=streak,
        weighted_average=weighted_avg,
        recommendation=recommendation,
        confidence=confidence
    )
