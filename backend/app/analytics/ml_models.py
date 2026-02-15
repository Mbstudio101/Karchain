import pandas as pd
import numpy as np
import xgboost as xgb
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import joblib
import os
import logging

from app.models import Game, PlayerStats, TeamStats, BettingOdds, Team, MLModelMetadata, Player
from app.models_nba_official import NBAOfficialPlayerStats
from app.database import SessionLocal

logger = logging.getLogger(__name__)

def _current_nba_season(reference: datetime = None) -> str:
    reference = reference or datetime.utcnow()
    start_year = reference.year if reference.month >= 7 else reference.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"

class FeatureEngineer:
    def __init__(self, db: Session):
        self.db = db

    def get_team_rolling_stats(self, team_id, date, window=10):
        """Get rolling average stats for a team before a specific date."""
        # This is tricky without game-by-game team stats.
        # We can aggregate player stats for that team.
        stats = self.db.query(
            func.sum(PlayerStats.points).label("points"),
            func.sum(PlayerStats.rebounds).label("rebounds"),
            func.sum(PlayerStats.assists).label("assists"),
            func.count(PlayerStats.game_id).label("player_games")
        ).join(Game, PlayerStats.game_id == Game.id).filter(
            PlayerStats.player_id.in_(
                self.db.query(Player.id).filter(Player.team_id == team_id)
            ),
            Game.game_date < date,
            Game.game_date >= date - timedelta(days=30) # approx window
        ).group_by(Game.id).limit(window).all()
        
        if not stats:
            return {"ppg": 0, "rpg": 0, "apg": 0}
            
        df = pd.DataFrame(stats)
        return {
            "ppg": df["points"].mean(),
            "rpg": df["rebounds"].mean(),
            "apg": df["assists"].mean()
        }

    def get_team_hustle_defense_stats(self, team_id, season):
        """Get aggregate hustle and defense stats for a team."""
        # Map our team ID to NBA team ID
        # This is a temporary hardcoded mapping until we add it to the database
        nba_team_mapping = {
            7: 1610612737,   # Atlanta Hawks
            26: 1610612738,  # Boston Celtics
            4: 1610612751,   # Brooklyn Nets
            17: 1610612766,  # Charlotte Hornets
            29: 1610612741,  # Chicago Bulls
            9: 1610612739,   # Cleveland Cavaliers
            14: 1610612742,  # Dallas Mavericks
            24: 1610612743,  # Denver Nuggets
            31: 1610612765,  # Detroit Pistons
            28: 1610612744,  # Golden State Warriors
            2: 1610612745,   # Houston Rockets
            27: 1610612754,  # Indiana Pacers
            32: 1610612746,  # Los Angeles Clippers
            13: 1610612747,  # Los Angeles Lakers
            5: 1610612763,   # Memphis Grizzlies
            3: 1610612748,   # Miami Heat
            11: 1610612749,  # Milwaukee Bucks
            25: 1610612750,  # Minnesota Timberwolves
            6: 1610612740,   # New Orleans Pelicans
            10: 1610612752,  # New York Knicks
            23: 1610612760,  # Oklahoma City Thunder
            19: 1610612753,  # Orlando Magic
            16: 1610612755,  # Philadelphia 76ers
            8: 1610612756,   # Phoenix Suns
            12: 1610612757,  # Portland Trail Blazers
            1: 1610612758,   # Sacramento Kings
            21: 1610612759,  # San Antonio Spurs
            22: 1610612761,  # Toronto Raptors
            15: 1610612762,  # Utah Jazz
            30: 1610612764,  # Washington Wizards
        }
        
        nba_team_id = nba_team_mapping.get(team_id)
        
        if not nba_team_id:
            logger.warning(f"No NBA team ID mapping for team {team_id}")
            return {
                "team_deflections": 0,
                "team_screen_assists": 0,
                "team_contested_shots": 0,
                "team_loose_balls": 0,
                "team_charges_drawn": 0,
                "team_defense_fg_diff": 0,
                "hustle_score": 0
            }
            
        # Get hustle stats for this team using the NBA team ID
        hustle_stats = self.db.query(
            func.sum(NBAOfficialPlayerStats.deflections).label("team_deflections"),
            func.sum(NBAOfficialPlayerStats.screen_assists).label("team_screen_assists"),
            func.sum(NBAOfficialPlayerStats.contested_shots).label("team_contested_shots"),
            func.sum(NBAOfficialPlayerStats.loose_balls_recovered).label("team_loose_balls"),
            func.sum(NBAOfficialPlayerStats.charges_drawn).label("team_charges_drawn"),
            func.avg(NBAOfficialPlayerStats.defense_fg_percentage_diff).label("team_defense_fg_diff"),
            func.count(NBAOfficialPlayerStats.player_id).label("players_with_stats")
        ).filter(
            NBAOfficialPlayerStats.team_id == nba_team_id,
            NBAOfficialPlayerStats.season == season,
            NBAOfficialPlayerStats.stat_type.in_(['hustle', 'defense'])
        ).first()
        
        if not hustle_stats or hustle_stats.players_with_stats == 0:
            return {
                "team_deflections": 0,
                "team_screen_assists": 0,
                "team_contested_shots": 0,
                "team_loose_balls": 0,
                "team_charges_drawn": 0,
                "team_defense_fg_diff": 0,
                "hustle_score": 0  # Composite hustle metric
            }
        
        # Calculate composite hustle score (higher is better)
        hustle_score = (
            (hustle_stats.team_deflections or 0) * 0.3 +
            (hustle_stats.team_screen_assists or 0) * 0.25 +
            (hustle_stats.team_contested_shots or 0) * 0.2 +
            (hustle_stats.team_loose_balls or 0) * 0.15 +
            (hustle_stats.team_charges_drawn or 0) * 0.1
        )
        
        return {
            "team_deflections": hustle_stats.team_deflections or 0,
            "team_screen_assists": hustle_stats.team_screen_assists or 0,
            "team_contested_shots": hustle_stats.team_contested_shots or 0,
            "team_loose_balls": hustle_stats.team_loose_balls or 0,
            "team_charges_drawn": hustle_stats.team_charges_drawn or 0,
            "team_defense_fg_diff": hustle_stats.team_defense_fg_diff or 0,
            "hustle_score": hustle_score
        }

    def prepare_training_data(self):
        """
        Prepare dataset for Moneyline/Spread prediction.
        Target: 1 if Home Win, 0 if Away Win.
        """
        games = self.db.query(Game).filter(Game.status == "Final").all()
        data = []
        
        season = _current_nba_season()
        for game in games:
            if not game.home_team or not game.away_team:
                continue
                
            # Features
            home_stats = self.get_team_rolling_stats(game.home_team_id, game.game_date)
            away_stats = self.get_team_rolling_stats(game.away_team_id, game.game_date)
            
            # Get hustle and defense stats for both teams
            home_hustle = self.get_team_hustle_defense_stats(game.home_team_id, season)
            away_hustle = self.get_team_hustle_defense_stats(game.away_team_id, season)
            
            row = {
                "home_ppg": home_stats["ppg"],
                "away_ppg": away_stats["ppg"],
                "home_rpg": home_stats["rpg"],
                "away_rpg": away_stats["rpg"],
                "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0,
                # New hustle and defense features
                "home_hustle_score": home_hustle["hustle_score"],
                "away_hustle_score": away_hustle["hustle_score"],
                "home_defense_fg_diff": home_hustle["team_defense_fg_diff"],
                "away_defense_fg_diff": away_hustle["team_defense_fg_diff"],
                "home_contested_shots": home_hustle["team_contested_shots"],
                "away_contested_shots": away_hustle["team_contested_shots"],
                # Target
                "target_home_win": 1 if game.home_score > game.away_score else 0,
                "target_spread_margin": game.home_score - game.away_score
            }
            data.append(row)
            
        return pd.DataFrame(data)

class NBAXGBoostModel:
    def __init__(self):
        self.model_path = "models/nba_xgb_v1.pkl"
        self.model = None
        
        # Try to load existing model
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info("Loaded existing XGBoost model.")
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
        
        if self.model is None:
            # Initialize fresh for training
            self.model = xgb.XGBClassifier(
                objective='binary:logistic',
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5
            )

    def train(self, df):

        if df.empty:
            logger.warning("No data to train on.")
            return None

        X = df.drop(columns=["target_home_win", "target_spread_margin"])
        y = df["target_home_win"]

        # Train/test split (80/20) for proper out-of-sample evaluation
        split_idx = int(len(X) * 0.8)
        if split_idx < 10:
            # Not enough data for a split; train on everything
            self.model.fit(X, y)
            accuracy = self.model.score(X, y)
            logger.info(f"Training Accuracy (no split, {len(X)} samples): {accuracy:.2f}")
        else:
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

            self.model.fit(X_train, y_train)

            train_acc = self.model.score(X_train, y_train)
            test_acc = self.model.score(X_test, y_test)
            accuracy = test_acc  # Report out-of-sample accuracy
            logger.info(f"Train Accuracy: {train_acc:.2f}, Test Accuracy: {test_acc:.2f} ({len(X_test)} test samples)")

        logger.info("Model trained successfully.")

        # Save
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.model, self.model_path)

        return accuracy

    def predict(self, features_df):
        if not os.path.exists(self.model_path):
            logger.warning("Model not found.")
            return None
            
        if not hasattr(self.model, "n_estimators"): # Check if loaded
            self.model = joblib.load(self.model_path)
            
        return self.model.predict_proba(features_df)[:, 1] # Return prob of Home Win

    def predict_one(self, game, db):
        engineer = FeatureEngineer(db)
        home_stats = engineer.get_team_rolling_stats(game.home_team_id, game.game_date)
        away_stats = engineer.get_team_rolling_stats(game.away_team_id, game.game_date)
        season = _current_nba_season()
        
        # Get hustle and defense stats
        home_hustle = engineer.get_team_hustle_defense_stats(game.home_team_id, season)
        away_hustle = engineer.get_team_hustle_defense_stats(game.away_team_id, season)

        row = {
            "home_ppg": home_stats["ppg"],
            "away_ppg": away_stats["ppg"],
            "home_rpg": home_stats["rpg"],
            "away_rpg": away_stats["rpg"],
            "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0,
            # New hustle and defense features
            "home_hustle_score": home_hustle["hustle_score"],
            "away_hustle_score": away_hustle["hustle_score"],
            "home_defense_fg_diff": home_hustle["team_defense_fg_diff"],
            "away_defense_fg_diff": away_hustle["team_defense_fg_diff"],
            "home_contested_shots": home_hustle["team_contested_shots"],
            "away_contested_shots": away_hustle["team_contested_shots"]
        }
        df = pd.DataFrame([row])

        result = self.predict(df)
        if result is None:
            return None
        return result[0]

def train_and_save_model():
    db = SessionLocal()
    try:
        engineer = FeatureEngineer(db)
        logger.info("Preparing training data...")
        df = engineer.prepare_training_data()
        
        logger.info(f"Training on {len(df)} games...")
        model = NBAXGBoostModel()
        acc = model.train(df)
        
        # Save metadata
        meta = MLModelMetadata(
            model_name="nba_xgb_moneyline",
            model_type="classifier",
            version="1.0",
            accuracy=acc,
            filepath=model.model_path,
            is_active=True
        )
        db.add(meta)
        db.commit()
        print(f"Model trained and saved with accuracy: {acc:.2%}")
        
    finally:
        db.close()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    train_and_save_model()
