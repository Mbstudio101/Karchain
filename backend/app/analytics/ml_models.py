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
from app.database import SessionLocal

logger = logging.getLogger(__name__)

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

    def prepare_training_data(self):
        """
        Prepare dataset for Moneyline/Spread prediction.
        Target: 1 if Home Win, 0 if Away Win.
        """
        games = self.db.query(Game).filter(Game.status == "Final").all()
        data = []
        
        for game in games:
            if not game.home_team or not game.away_team:
                continue
                
            # Features
            home_stats = self.get_team_rolling_stats(game.home_team_id, game.game_date)
            away_stats = self.get_team_rolling_stats(game.away_team_id, game.game_date)
            
            row = {
                "home_ppg": home_stats["ppg"],
                "away_ppg": away_stats["ppg"],
                "home_rpg": home_stats["rpg"],
                "away_rpg": away_stats["rpg"],
                "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0,
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

        row = {
            "home_ppg": home_stats["ppg"],
            "away_ppg": away_stats["ppg"],
            "home_rpg": home_stats["rpg"],
            "away_rpg": away_stats["rpg"],
            "is_home_conference_match": 1 if game.home_team.conference == game.away_team.conference else 0
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
