# NBA Reconstructed Data Integration - Mathematical Documentation

## Overview
This document details the mathematical calculations and data points used in the Karchain NBA prediction engine's reconstructed data integration system. The system leverages reconstructed clutch performance, tracking metrics, and advanced analytics to enhance AI Parlay Generator and Genius Picks accuracy.

## Data Sources and Reconstruction

### 1. Clutch Performance Analytics
**Source**: Reconstructed from ESPN, Yahoo Sports, Basketball Reference
**Key Metrics**:
- **CLUTCH_RATING**: Weighted performance in 4th quarter & OT (0.0-1.0 scale)
- **CLUTCH_USAGE_RATE**: Usage percentage in clutch situations
- **CLUTCH_EFG_PCT**: Effective field goal percentage in clutch

**Mathematical Formula**:
```
CLUTCH_RATING = (0.4 × 4Q_PTS_PER_MIN + 0.3 × OT_PTS_PER_MIN + 0.2 × 4Q_AST_PER_MIN + 0.1 × 4Q_REB_PER_MIN) / LEAGUE_AVG
```

### 2. Tracking Metrics
**Source**: Reconstructed from player movement data and game logs
**Key Metrics**:
- **TRACKING_SPEED**: Average speed in mph during games
- **TRACKING_DISTANCE**: Total distance covered per game
- **TRACKING_DFG_PCT**: Defensive field goal percentage against

**Athletic Composite Score**:
```
ATHLETIC_COMPOSITE = (TRACKING_SPEED / 6.0) × 0.6 + (TRACKING_DISTANCE / 5.0) × 0.4
```

### 3. Defensive Impact
**TRACKING_DFG_PCT**: Percentage of shots defended successfully
**Calculation**:
```
DEFENSIVE_IMPACT = 1 - TRACKING_DFG_PCT
```

## Enhanced Probability Calculations

### Base Hit Rate Calculation
```python
def calculate_base_hit_rate(player_stats, prop_type, line):
    hits = 0
    for stat in player_stats[-20:]:  # Last 20 games
        if prop_type == 'points':
            value = stat.points or 0
        elif prop_type == 'rebounds':
            value = stat.rebounds or 0
        elif prop_type == 'assists':
            value = stat.assists or 0
        elif prop_type == 'pts+reb+ast':
            value = (stat.points or 0) + (stat.rebounds or 0) + (stat.assists or 0)
        
        if value > line:
            hits += 1
    
    return hits / len(player_stats[-20:])
```

### Enhanced Probability with Reconstructed Data
```python
def calculate_enhanced_probability(base_prob, clutch_score, athletic_score, 
                                 defensive_score, game_context):
    # Clutch adjustment for close games
    clutch_adjustment = 0.0
    if game_context['is_close_game']:
        clutch_adjustment = (clutch_score - 0.5) × 0.15
    
    # Athletic adjustment for physical props
    athletic_adjustment = 0.0
    if prop_type in ['points', 'rebounds', 'pts+reb+ast']:
        athletic_adjustment = (athletic_score - 0.5) × 0.10
    
    # Defensive adjustment
    defensive_adjustment = (0.5 - defensive_score) × 0.08
    
    # Consistency adjustment
    consistency_adjustment = (consistency_score - 0.5) × 0.05
    
    enhanced_prob = base_prob + clutch_adjustment + athletic_adjustment + 
                   defensive_adjustment + consistency_adjustment
    
    return max(0.05, min(0.95, enhanced_prob))
```

## Expected Value (EV) Calculations

### Base EV Formula
```python
def calculate_base_ev(probability, odds, stake=100):
    if odds > 0:
        decimal_odds = 1 + (odds / 100)
    else:
        decimal_odds = 1 + (100 / abs(odds))
    
    return (probability × decimal_odds × stake) - stake
```

### Enhanced EV with Confidence Multipliers
```python
def calculate_enhanced_ev(base_ev, confidence, composite_rating):
    # Confidence multiplier (0.5 to 1.0)
    confidence_multiplier = 0.5 + (confidence × 0.5)
    
    # Rating multiplier based on player quality (0.7 to 1.0)
    rating_multiplier = 0.7 + (composite_rating × 0.3)
    
    enhanced_ev = base_ev × confidence_multiplier × rating_multiplier
    
    return {
        'ev': enhanced_ev,
        'edge': enhanced_ev / 100,  # As percentage
        'confidence_multiplier': confidence_multiplier,
        'rating_multiplier': rating_multiplier
    }
```

## Kelly Criterion Optimization

### Standard Kelly Criterion
```python
def kelly_criterion(probability, odds):
    if odds > 0:
        decimal = 1 + (odds / 100)
    else:
        decimal = 1 + (100 / abs(odds))
    
    b = decimal - 1  # Net odds
    q = 1 - probability
    
    return (b × probability - q) / b
```

### Enhanced Kelly with Confidence
```python
def enhanced_kelly_criterion(probability, odds, confidence):
    base_kelly = kelly_criterion(probability, odds)
    adjusted_kelly = base_kelly × confidence × 0.5  # Half Kelly for safety
    
    return max(0, min(adjusted_kelly, 0.05))  # Cap at 5%
```

## Confidence Intervals (Wilson Score)

### Wilson Confidence Interval Formula
```python
def wilson_confidence_interval(successes, trials, z=1.96):
    if trials == 0:
        return (0.0, 1.0)
    
    p = successes / trials
    n = trials
    
    center = (p + z²/(2×n)) / (1 + z²/n)
    margin = z × sqrt((p×(1-p) + z²/(4×n)) / n) / (1 + z²/n)
    
    ci_low = max(0.0, center - margin)
    ci_high = min(1.0, center + margin)
    
    return (ci_low, ci_high)
```

## Grading System

### Enhanced Grade Calculation
```python
def calculate_grade(ev, edge, composite_rating, streak_status):
    # Base requirements
    if ev > 8 and edge > 0.12 and composite_rating > 0.8 and streak == "hot":
        return "S"
    elif ev > 5 and edge > 0.08 and composite_rating > 0.7:
        return "A+"
    elif ev > 3 and edge > 0.05 and composite_rating > 0.6:
        return "A"
    elif ev > 2 and edge > 0.03 and composite_rating > 0.5:
        return "B+"
    else:
        return "B"
```

## Risk Assessment

### Parlay Risk Score Calculation
```python
def calculate_parlay_risk(bets):
    risk_factors = []
    
    for bet in bets:
        # Edge-based risk
        edge = bet.get('edge', 0)
        if edge < 0.03:
            risk_factors.append(8.0)
        elif edge < 0.05:
            risk_factors.append(5.0)
        else:
            risk_factors.append(2.0)
        
        # Confidence-based risk
        confidence = bet.get('confidence_score', 0.6)
        if confidence < 0.5:
            risk_factors.append(7.0)
        elif confidence < 0.6:
            risk_factors.append(4.0)
        else:
            risk_factors.append(1.0)
        
        # Prop type risk
        if bet['type'] == 'game':
            risk_factors.append(6.0)  # Games are riskier
        else:
            risk_factors.append(3.0)
    
    avg_risk = sum(risk_factors) / len(risk_factors)
    leg_penalty = len(bets) × 0.5
    
    return min(10.0, avg_risk + leg_penalty)
```

## Data Integration Features

### 1. Clutch Performance Integration
- **Use Case**: Close games (point differential < 5)
- **Impact**: ±15% probability adjustment
- **Data Points**: 4Q scoring, OT performance, clutch usage rate

### 2. Athletic Metrics Integration
- **Use Case**: Physical performance props (points, rebounds, combined)
- **Impact**: ±10% probability adjustment
- **Data Points**: Speed, distance, athletic composite score

### 3. Defensive Impact Integration
- **Use Case**: Offensive props against defensive players
- **Impact**: ±8% probability adjustment
- **Data Points**: Defensive FG%, defensive rating

### 4. Consistency Scoring
- **Use Case**: All prop types for reliability assessment
- **Impact**: ±5% probability adjustment
- **Data Points**: Clutch usage rate, clutch efficiency

## Feature Vector Generation

### Player Feature Vector
```python
def generate_player_feature_vector(player_id):
    features = {
        'clutch_rating': clutch_data.get('CLUTCH_RATING', 0.5),
        'defensive_impact': 1 - tracking_data.get('TRACKING_DFG_PCT', 0.45),
        'athletic_performance': (speed / 6.0) * 0.6 + (distance / 5.0) * 0.4,
        'consistency_score': (clutch_usage * 0.3) + (clutch_efg * 0.7),
        'composite_rating': (clutch_score * 0.4 + athletic_score * 0.3 + 
                           defensive_score * 0.2 + consistency_score * 0.1)
    }
    
    return features
```

## Risk Level Optimization

### Conservative Strategy
- **Prop Allocation**: 70% props, 30% games
- **Minimum Edge**: 6%
- **Kelly Fraction**: 0.5× standard
- **Focus**: High-confidence, low-variance bets

### Balanced Strategy
- **Prop Allocation**: 60% props, 40% games
- **Minimum Edge**: 4%
- **Kelly Fraction**: 0.5× standard
- **Focus**: Optimal risk-reward balance

### Aggressive Strategy
- **Prop Allocation**: 40% props, 60% games
- **Minimum Edge**: 3%
- **Kelly Fraction**: 0.5× standard
- **Focus**: Higher variance, higher potential returns

## Security and Validation

### Data Integrity Checks
- SHA-256 hashing for all data entries
- Audit trails for data modifications
- Quality scoring based on completeness and accuracy

### Validation Metrics
- **Completeness**: Percentage of expected data points available
- **Accuracy**: Correlation with actual game outcomes
- **Consistency**: Stability of metrics over time
- **Freshness**: Recency of data updates

This mathematical framework ensures that the AI Parlay Generator and Genius Picks systems leverage all available reconstructed NBA data to make optimal betting decisions while maintaining appropriate risk management and statistical rigor.