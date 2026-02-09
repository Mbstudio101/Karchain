from .base_scraper import BaseScraper
from bs4 import BeautifulSoup
import logging
import asyncio
from app.database import SessionLocal
from app.models import Player, Team, PlayerStats, TeamStats
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)

class NBAScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.db: Session = SessionLocal()

    async def scrape_team_stats(self):
        """Scrapes team stats from NBA.com/stats API using requests."""
        url = "https://stats.nba.com/stats/leaguedashteamstats"
        params = {
            "MeasureType": "Base",
            "PerMode": "PerGame",
            "PlusMinus": "N",
            "PaceAdjust": "N",
            "Rank": "N",
            "LeagueID": "00",
            "Season": "2024-25",
            "SeasonType": "Regular Season",
            "PORound": "0",
            "Outcome": "",
            "Location": "",
            "Month": "0",
            "SeasonSegment": "",
            "DateFrom": "",
            "DateTo": "",
            "OpponentTeamID": "0",
            "VsConference": "",
            "VsDivision": "",
            "TeamID": "0",
            "Conference": "",
            "Division": "",
            "GameSegment": "",
            "Period": "0",
            "ShotClockRange": "",
            "LastNGames": "0"
        }
        headers = {
            "Host": "stats.nba.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Connection": "keep-alive",
            "Referer": "https://www.nba.com/",
            "Origin": "https://www.nba.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        try:
            import requests
            logger.info(f"Fetching team stats from {url}...")
            # Use requests directly, no Playwright needed for this endpoint if headers are correct
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            result_sets = data.get("resultSets", [])
            if not result_sets:
                logger.error("No resultSets in response.")
                return

            headers_list = result_sets[0]["headers"]
            row_set = result_sets[0]["rowSet"]
            
            # Map headers to indices
            idx = {h: i for i, h in enumerate(headers_list)}
            
            logger.info(f"Found {len(row_set)} team stats rows.")

            for row in row_set:
                team_name = row[idx["TEAM_NAME"]]
                wins = row[idx["W"]]
                losses = row[idx["L"]]
                win_pct = row[idx["W_PCT"]]
                ppg = row[idx["PTS"]]
                plus_minus = row[idx["PLUS_MINUS"]]
                
                # Calculate opponent ppg
                opp_ppg = ppg - plus_minus
                
                self.save_team_stats(team_name, wins, losses, win_pct, ppg, opp_ppg, plus_minus)

        except Exception as e:
            logger.error(f"Error scraping team stats: {e}")
            
    def save_team_stats(self, team_name: str, wins: int, losses: int, win_pct: float, ppg: float, opp_ppg: float, plus_minus: float):
        team = self.db.query(Team).filter(Team.name == team_name).first()
        if not team:
            team = Team(name=team_name, sport="NBA")
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)
        
        # Update team record
        team.current_record = f"{wins}-{losses}"
        
        # Check if stats for this season already exist to avoid duplicates
        existing_stats = self.db.query(TeamStats).filter(
            TeamStats.team_id == team.id,
            TeamStats.season == "2024-25"
        ).first()

        if existing_stats:
            existing_stats.wins = wins
            existing_stats.losses = losses
            existing_stats.win_pct = win_pct
            existing_stats.ppg = ppg
            existing_stats.opp_ppg = opp_ppg
            existing_stats.plus_minus = plus_minus
            existing_stats.timestamp = datetime.utcnow()
            logger.info(f"Updated stats for {team_name}")
        else:
            stats = TeamStats(
                team_id=team.id,
                season="2024-25",
                wins=wins,
                losses=losses,
                win_pct=win_pct,
                ppg=ppg,
                opp_ppg=opp_ppg,
                plus_minus=plus_minus
            )
            self.db.add(stats)
            logger.info(f"Saved stats for {team_name}")
        
        self.db.commit()


    async def scrape_players(self):
        """Scrapes player data from NBA.com/players using Next.js hydration data."""
        url = "https://www.nba.com/players"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            # Use requests for the initial HTML fetch as it's more reliable for this specific page structure
            # and avoids some headless browser issues with the initial load.
            import requests
            import json
            
            logger.info(f"Fetching {url}...")
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            
            if not next_data_script:
                logger.error("Could not find __NEXT_DATA__ script tag.")
                return

            data = json.loads(next_data_script.string)
            if "props" in data and "pageProps" in data["props"] and "players" in data["props"]["pageProps"]:
                players_list = data["props"]["pageProps"]["players"]
                logger.info(f"Found {len(players_list)} players.")
                
                for p in players_list:
                    first_name = p.get('PLAYER_FIRST_NAME', '')
                    last_name = p.get('PLAYER_LAST_NAME', '')
                    full_name = f"{first_name} {last_name}".strip()
                    team_city = p.get('TEAM_CITY', '')
                    team_name_attr = p.get('TEAM_NAME', '')
                    team_name = f"{team_city} {team_name_attr}".strip() if team_city and team_name_attr else team_name_attr
                    
                    # Handle cases where team is null or empty (free agents)
                    if not team_name:
                        team_name = "Free Agent"
                    
                    position = p.get('POSITION', '')
                    
                    self.save_player(full_name, team_name, position)
            else:
                logger.error("JSON structure did not match expected format.")

        except Exception as e:
            logger.error(f"Error scraping players: {e}")
            raise


    async def scrape_player_stats(self):
        """Scrapes player game logs from NBA.com/stats API using requests."""
        url = "https://stats.nba.com/stats/leaguegamelog"
        params = {
            "Counter": "1000",
            "DateFrom": "",
            "DateTo": "",
            "Direction": "DESC",
            "LeagueID": "00",
            "PlayerOrTeam": "P",
            "Season": "2024-25",
            "SeasonType": "Regular Season",
            "Sorter": "DATE"
        }
        headers = {
            "Host": "stats.nba.com",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "x-nba-stats-origin": "stats",
            "x-nba-stats-token": "true",
            "Connection": "keep-alive",
            "Referer": "https://www.nba.com/",
            "Origin": "https://www.nba.com",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

        try:
            import requests
            logger.info(f"Fetching player stats from {url}...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            result_sets = data.get("resultSets", [])
            if not result_sets:
                logger.error("No resultSets in response.")
                return

            headers_list = result_sets[0]["headers"]
            row_set = result_sets[0]["rowSet"]
            
            idx = {h: i for i, h in enumerate(headers_list)}
            
            logger.info(f"Found {len(row_set)} player game logs.")
            
            # Cache players to avoid repetitive DB queries
            players_cache = {p.name: p.id for p in self.db.query(Player).all()}
            
            count = 0
            for row in row_set:
                player_name = row[idx["PLAYER_NAME"]]
                
                # Check cache
                if player_name not in players_cache:
                    # Try to match partially or skip?
                    # For now skip or handle later. 
                    # Actually we should try to add them if missing? 
                    # But we scraped players already.
                    continue
                
                player_id = players_cache[player_name]
                game_date_str = row[idx["GAME_DATE"]] # "2023-10-24"
                
                try:
                    game_date = datetime.strptime(game_date_str, "%Y-%m-%d").date()
                except ValueError:
                    continue

                matchup = row[idx["MATCHUP"]] # "BOS vs. NYK" or "BOS @ NYK"
                opponent = matchup.split(" ")[-1]
                
                pts = row[idx["PTS"]]
                reb = row[idx["REB"]]
                ast = row[idx["AST"]]
                stl = row[idx["STL"]]
                blk = row[idx["BLK"]]
                min_str = str(row[idx["MIN"]]) # sometimes minutes is MM:SS or float
                try:
                    minutes = float(min_str)
                except:
                     minutes = 0.0 # Handle "MM:SS" if needed, but API usually returns float? 
                     # Actually headers say MIN usually, but let's check sample.
                     # Sample has integer for MIN e.g. 24.
                
                fg_pct = row[idx["FG_PCT"]]
                fg3_pct = row[idx["FG3_PCT"]]
                
                self.save_player_stats(
                    player_id=player_id,
                    game_date=game_date,
                    opponent=opponent,
                    points=pts,
                    rebounds=reb,
                    assists=ast,
                    steals=stl,
                    blocks=blk,
                    minutes=minutes,
                    fg_pct=fg_pct,
                    fg3_pct=fg3_pct
                )
                count += 1
                if count % 1000 == 0:
                    logger.info(f"Processed {count} logs...")
                    self.db.commit() # Commit periodically

            self.db.commit()
            logger.info("Finished saving player stats.")

        except Exception as e:
            logger.error(f"Error scraping player stats: {e}")

    def save_player_stats(self, player_id, game_date, opponent, points, rebounds, assists, steals, blocks, minutes, fg_pct, fg3_pct):
        # Check explicit duplicate (player + date)
        # Assuming we don't have multiple games per day for a player
        exists = self.db.query(PlayerStats).filter(
            PlayerStats.player_id == player_id,
            PlayerStats.game_date == game_date
        ).first()
        
        if not exists:
            stats = PlayerStats(
                player_id=player_id,
                game_date=game_date,
                opponent=opponent,
                points=points,
                rebounds=rebounds,
                assists=assists,
                steals=steals,
                blocks=blocks,
                minutes_played=minutes,
                fg_percentage=fg_pct,
                three_pt_percentage=fg3_pct
            )
            self.db.add(stats)

    def save_player(self, name: str, team_name: str, position: str = None):
        """Saves player to database."""
        team = self.db.query(Team).filter(Team.name == team_name).first()
        if not team:
            team = Team(name=team_name, sport="NBA")
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)
        
        player = self.db.query(Player).filter(Player.name == name, Player.team_id == team.id).first()
        if not player:
            player = Player(name=name, team_id=team.id, position=position, sport="NBA")
            self.db.add(player)
            self.db.commit()
            logger.info(f"Saved player: {name} ({team_name})")
        else:
            logger.info(f"Player already exists: {name}")

    async def close(self):
        self.db.close()
        await self.stop()
