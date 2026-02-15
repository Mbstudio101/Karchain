from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from nba_api.stats.endpoints import leaguegamelog
import logging
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def sync_player_stats_from_nba(season='2025-26'):
    """
    Syncs player game logs (stats) from NBA.com for the specified season.
    Creates players if they don't exist.
    """
    logger.info(f"Starting player stats sync for season {season}...")
    db = SessionLocal()
    
    try:
        # Fetch all game logs for the season
        log = leaguegamelog.LeagueGameLog(
            season=season, 
            player_or_team_abbreviation='P', 
            season_type_all_star='Regular Season'
        )
        df = log.get_data_frames()[0]
        
        if df.empty:
            logger.warning("No player stats found.")
            return

        logger.info(f"Found {len(df)} player stats records. Processing...")
        
        # Get existing players to minimize queries
        existing_players = {p.id for p in db.query(models.Player.id).all()}
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        stats_to_add = []
        
        # Track existing stats to avoid duplicates (player_id + game_date)
        # We'll use a composite key for checking existence
        # Since checking DB for every row is slow, we'll fetch all existing stats first?
        # That might be too big.
        # Instead, we can delete all stats for this season and re-insert?
        # Or just upsert.
        # Given 17k records, deleting and re-inserting is actually fast enough and cleaner.
        
        # But we need to be careful not to delete stats from other sources if any.
        # Assuming this is the only source.
        
        # Let's try to just insert new ones or update.
        # For simplicity and speed, let's look up existing players first.
        
        unique_players_in_df = df[['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID']].drop_duplicates('PLAYER_ID')
        
        for _, row in unique_players_in_df.iterrows():
            p_id = int(row['PLAYER_ID'])
            if p_id not in existing_players:
                # Create new player
                new_player = models.Player(
                    id=p_id,
                    name=row['PLAYER_NAME'],
                    team_id=int(row['TEAM_ID']) if not pd.isna(row['TEAM_ID']) else None,
                    sport='basketball',
                    active_status=True
                )
                db.add(new_player)
                existing_players.add(p_id)
        
        db.commit() # Commit new players
        
        # Now process stats
        # To avoid duplicates, we can query existing stats count.
        # If we want to be robust, we should check existence.
        # Let's delete stats for the current season range to ensure clean state.
        # Determine date range from DF
        min_date = df['GAME_DATE'].min()
        max_date = df['GAME_DATE'].max()
        
        # Convert string dates to objects
        min_date_obj = datetime.strptime(min_date, '%Y-%m-%d').date()
        max_date_obj = datetime.strptime(max_date, '%Y-%m-%d').date()
        
        logger.info(f"Clearing existing stats between {min_date} and {max_date}...")
        db.query(models.PlayerStats).filter(
            models.PlayerStats.game_date >= min_date_obj,
            models.PlayerStats.game_date <= max_date_obj
        ).delete(synchronize_session=False)
        db.commit()
        
        logger.info("Inserting new stats...")
        
        count = 0
        for _, row in df.iterrows():
            # Parse opponent from MATCHUP (e.g. "OKC vs. HOU" or "OKC @ HOU")
            matchup = row['MATCHUP']
            team_abbr = row['TEAM_ABBREVIATION']
            
            # Opponent is the other team in matchup
            # This is a bit rough, but sufficient.
            # Usually matchup is "AAA vs. BBB" or "AAA @ BBB"
            parts = matchup.replace(' vs. ', ' ').replace(' @ ', ' ').split(' ')
            if len(parts) == 2:
                opponent = parts[1] if parts[0] == team_abbr else parts[0]
            else:
                opponent = "UNK"

            # Handle NaN values
            def val(x):
                return 0 if pd.isna(x) else x

            stat = models.PlayerStats(
                player_id=int(row['PLAYER_ID']),
                game_date=datetime.strptime(row['GAME_DATE'], '%Y-%m-%d').date(),
                opponent=opponent,
                points=val(row['PTS']),
                rebounds=val(row['REB']),
                assists=val(row['AST']),
                steals=val(row['STL']),
                blocks=val(row['BLK']),
                turnovers=val(row['TOV']),
                three_pointers=val(row['FG3M']),
                minutes_played=val(row['MIN']),
                fg_percentage=val(row['FG_PCT']) * 100 if not pd.isna(row['FG_PCT']) else 0,
                three_pt_percentage=val(row['FG3_PCT']) * 100 if not pd.isna(row['FG3_PCT']) else 0
            )
            db.add(stat)
            count += 1
            
            if count % 1000 == 0:
                db.commit()
                logger.info(f"Processed {count} records...")
                
        db.commit()
        logger.info(f"Successfully synced {count} player stats records.")
        
    except Exception as e:
        logger.error(f"Error syncing player stats: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_player_stats_from_nba()
