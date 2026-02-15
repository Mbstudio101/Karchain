import asyncio
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .base_scraper import BaseScraper
from app.database import SessionLocal
from app.models import Team, Game, BettingOdds, Player, PlayerProps

logger = logging.getLogger(__name__)

def decimal_to_american(decimal_odds):
    """Convert decimal odds to American odds."""
    if not decimal_odds or decimal_odds <= 1:
        return -110  # Default to -110 for invalid odds
    if decimal_odds >= 2:
        return min(int((decimal_odds - 1) * 100), 300)  # Cap at +300 for realistic props
    else:
        return max(int(-100 / (decimal_odds - 1)), -400)  # Cap at -400 for realistic props

class BettingProsScraper(BaseScraper):
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        self.api_url = "https://api.bettingpros.com/v3"
        self.headers = {
            "x-api-key": "CHi8Hy5CEE4khd46XNYL23dCFX96oUdw6qOt1Dnh",
            "referer": "https://www.bettingpros.com/",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        self.game_markets = {
            127: "moneyline",
            128: "total",
            129: "spread",
            # Additional Game Props
            130: "team_total_home",     # Home team total points
            131: "team_total_away",     # Away team total points
            132: "first_half_spread",   # First half spread
            133: "first_half_total",    # First half total
            134: "first_quarter_spread", # First quarter spread
            135: "first_quarter_total", # First quarter total
            247: "first_half_moneyline", # First half moneyline
            248: "first_quarter_moneyline", # First quarter moneyline
            # Advanced Game Props
            350: "win_margin_home",     # Home team win margin
            351: "win_margin_away",     # Away team win margin
            352: "race_to_10_home",     # Race to 10 points - home
            353: "race_to_10_away",     # Race to 10 points - away
            354: "race_to_20_home",     # Race to 20 points - home
            355: "race_to_20_away",     # Race to 20 points - away
            356: "highest_scoring_quarter", # Highest scoring quarter
            357: "both_teams_score_100",    # Both teams score 100+ points
            358: "overtime_yes_no",         # Game goes to overtime
            359: "double_result",           # Double result (HT/FT)
            363: "total_points_odd_even",   # Total points odd/even
            364: "team_total_odd_even_home", # Home team total odd/even
        }
        # Player Prop Market IDs (verified via API discovery)
        # Note: Some market IDs may return player props, others return team props
        self.prop_markets = {
            # Core Individual Stats (verified working with player props)
            156: "points",        # Player points O/U (e.g. 7.5, 15.5, etc.)
            157: "assists",       # Player assists O/U (e.g. 5.5)
            159: "rebounds",      # Player rebounds O/U 
            151: "threes",        # Player 3-pointers O/U (e.g. 2.5)
            142: "steals",        # Player steals O/U (e.g. 1)
            162: "blocks",        # Player blocks O/U (e.g. 1.5)
            160: "turnovers",     # Player turnovers O/U (e.g. 0.5)
            # Specialty Player Props
            136: "double_double", # To record a double-double (Yes/No)
            152: "first_basket",  # First basket scorer (Yes/No with 0.5 line)
            # Combo Stats (if available)
            335: "pts+reb",       # Points + Rebounds combo
            336: "pts+ast",       # Points + Assists combo
            337: "reb+ast",       # Rebounds + Assists combo
            338: "pts+reb+ast",   # Points + Rebounds + Assists combo (PRA)
        }
        # NBA team abbreviation mapping
        self.NBA_TEAMS = {
            "ATL": "Atlanta Hawks", 
            "BOS": "Boston Celtics", 
            "BKN": "Brooklyn Nets",
            "CHA": "Charlotte Hornets", 
            "CHI": "Chicago Bulls", 
            "CLE": "Cleveland Cavaliers",
            "DAL": "Dallas Mavericks", 
            "DEN": "Denver Nuggets", 
            "DET": "Detroit Pistons",
            "GSW": "Golden State Warriors", "GS": "Golden State Warriors",
            "HOU": "Houston Rockets", 
            "IND": "Indiana Pacers", 
            "LAC": "Los Angeles Clippers",
            "LAL": "Los Angeles Lakers", 
            "MEM": "Memphis Grizzlies",
            "MIA": "Miami Heat",
            "MIL": "Milwaukee Bucks", 
            "MIN": "Minnesota Timberwolves", 
            "NOR": "New Orleans Pelicans",
            "NOP": "New Orleans Pelicans", "NO": "New Orleans Pelicans",
            "NYK": "New York Knicks", "NY": "New York Knicks",
            "OKC": "Oklahoma City Thunder", 
            "ORL": "Orlando Magic", 
            "PHI": "Philadelphia 76ers",
            "PHX": "Phoenix Suns", "PHO": "Phoenix Suns", 
            "POR": "Portland Trail Blazers",
            "SAC": "Sacramento Kings", 
            "SAS": "San Antonio Spurs", "SA": "San Antonio Spurs",
            "TOR": "Toronto Raptors", 
            "UTH": "Utah Jazz", "UTA": "Utah Jazz",
            "WAS": "Washington Wizards"
        }
        self.events_cache = {} # event_id -> {home, away, game_id}

    def _parse_event_datetime(self, event: Dict) -> Optional[datetime]:
        """Best-effort parse of event start datetime from BettingPros payload."""
        for key in ("date", "start_time", "starts_at", "start", "scheduled", "commence_time"):
            raw = event.get(key)
            if not raw:
                continue
            try:
                if isinstance(raw, (int, float)):
                    return datetime.utcfromtimestamp(raw)
                text = str(raw).replace("Z", "+00:00")
                dt = datetime.fromisoformat(text)
                # Normalize to naive UTC for DB comparisons.
                return dt.replace(tzinfo=None) if dt.tzinfo else dt
            except Exception:
                continue
        return None

    def _find_existing_scoreboard_game(
        self,
        db,
        home_team_id: int,
        away_team_id: int,
        event_dt: Optional[datetime],
    ) -> Optional[Game]:
        """
        Resolve BettingPros event to an existing game row (created by ESPN scoreboard sync).
        Never creates games from BettingPros.
        """
        query = db.query(Game).filter(
            Game.home_team_id == home_team_id,
            Game.away_team_id == away_team_id
        )

        if event_dt:
            # Tight window around event start to avoid cross-day mismatches.
            start = event_dt - timedelta(hours=12)
            end = event_dt + timedelta(hours=12)
            return query.filter(
                Game.game_date >= start,
                Game.game_date < end
            ).order_by(Game.game_date.asc()).first()

        # Fallback: upcoming-only narrow window if event payload has no start timestamp.
        now = datetime.utcnow()
        return query.filter(
            Game.game_date >= now - timedelta(hours=6),
            Game.game_date <= now + timedelta(days=3)
        ).order_by(Game.game_date.asc()).first()

    def _get_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Request failed for {endpoint}: {e}")
            return None

    async def scrape_player_props_by_name(self, player_name: str):
        """
        Scrape player props for a specific player by name.
        This uses the API to find the player and their props.
        """
        logger.info(f"Scraping props for player: {player_name}")
        
        # First, try to find the player in the API
        player_data = self._get_api("players", {"name": player_name, "sport": "NBA"})
        if not player_data or not player_data.get("players"):
            logger.warning(f"Player not found: {player_name}")
            return
        
        # Get the first matching player
        player_info = player_data["players"][0]
        player_id = player_info.get("id")
        full_name = f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip()
        
        logger.info(f"Found player: {full_name} (ID: {player_id})")
        
        # Get props for this player
        props_data = self._get_api("props", {
            "player_id": player_id,
            "sport": "NBA",
            "limit": 100
        })
        
        if not props_data or not props_data.get("props"):
            logger.warning(f"No props found for player: {full_name}")
            return
        
        logger.info(f"Found {len(props_data['props'])} props for {full_name}")
        
        # Process each prop
        for prop in props_data["props"]:
            await self._process_individual_player_prop(prop, full_name)

    async def _process_individual_player_prop(self, prop: Dict, player_name: str):
        """Process a single player prop from the API."""
        try:
            # Extract event info
            event_id = str(prop.get("event_id"))
            market_id = prop.get("market_id")
            
            # Get event details if not cached
            if event_id not in self.events_cache:
                event_data = self._get_api("events", {"id": event_id})
                if event_data and event_data.get("events"):
                    event = event_data["events"][0]
                    home_abbr = event.get("home")
                    away_abbr = event.get("visitor")
                    
                    home_name = self.NBA_TEAMS.get(home_abbr)
                    away_name = self.NBA_TEAMS.get(away_abbr)
                    
                    # Find game in database
                    db = SessionLocal()
                    try:
                        home_team = db.query(Team).filter(Team.name == home_name).first() if home_name else None
                        away_team = db.query(Team).filter(Team.name == away_name).first() if away_name else None
                        
                        if home_team and away_team:
                            # Look for upcoming games
                            from datetime import timedelta
                            today = datetime.utcnow().date()
                            tomorrow = today + timedelta(days=2)
                            
                            game = db.query(Game).filter(
                                Game.home_team_id == home_team.id,
                                Game.away_team_id == away_team.id,
                                Game.game_date >= today,
                                Game.game_date <= tomorrow
                            ).first()
                            
                            self.events_cache[event_id] = {
                                "home": home_team.name,
                                "away": away_team.name,
                                "game_id": game.id if game else None
                            }
                    finally:
                        db.close()
                else:
                    return
            
            event_info = self.events_cache[event_id]
            if not event_info.get("game_id"):
                return
            
            # Map market ID to prop type
            market_map = {
                156: "points",
                157: "assists",
                159: "rebounds",
                151: "threes",
                142: "steals",
                162: "blocks",
                160: "turnovers",
                136: "double_double",
                152: "first_basket",
                335: "pts+reb",
                336: "pts+ast",
                337: "reb+ast",
                338: "pts+reb+ast"
            }
            
            prop_type = market_map.get(market_id)
            if not prop_type:
                return
            
            # Extract odds data
            over_data = prop.get("over", {})
            under_data = prop.get("under", {})
            
            line = over_data.get("line") or under_data.get("line")
            over_odds = over_data.get("odds", -110)
            under_odds = under_data.get("odds", -110)
            
            if not line:
                return
            
            # Convert decimal odds to American if needed
            if isinstance(over_odds, float):
                over_odds = decimal_to_american(over_odds)
            if isinstance(under_odds, float):
                under_odds = decimal_to_american(under_odds)
            
            # Get player's team
            player_team_abbr = prop.get("participant", {}).get("player", {}).get("team")
            player_team_name = self.NBA_TEAMS.get(player_team_abbr) if player_team_abbr else None
            
            # Use player's team if available, otherwise use home team
            target_team = player_team_name or event_info["home"]
            
            # Save the prop
            self.save_player_prop(player_name, prop_type, line, over_odds, under_odds, target_team, "BettingPros", game_id=event_info.get("game_id"))
            
            logger.info(f"Saved {prop_type} prop for {player_name}: {line} (O: {over_odds}, U: {under_odds})")
            
        except Exception as e:
            logger.error(f"Error processing individual player prop: {e}")

    async def scrape_nba_data(self):
        """Scrapes all NBA game lines and player props."""
        # 1. Fetch Events for both today and tomorrow
        from datetime import timedelta
        
        today = datetime.utcnow()
        tomorrow = today + timedelta(days=1)
        
        all_events = []
        
        # Fetch today's events
        today_str = today.strftime("%Y-%m-%d")
        events_data = self._get_api("events", {
            "sport": "NBA", 
            "date": today_str,
            "lineups": "true"
        })
        if events_data and events_data.get("events"):
            all_events.extend(events_data["events"])
            logger.info(f"Found {len(events_data['events'])} events for today ({today_str})")
        else:
            logger.warning(f"No events found for today ({today_str})")
        
        # Fetch tomorrow's events
        tomorrow_str = tomorrow.strftime("%Y-%m-%d")
        events_data_tomorrow = self._get_api("events", {
            "sport": "NBA", 
            "date": tomorrow_str,
            "lineups": "true"
        })
        if events_data_tomorrow and events_data_tomorrow.get("events"):
            all_events.extend(events_data_tomorrow["events"])
            logger.info(f"Found {len(events_data_tomorrow['events'])} events for tomorrow ({tomorrow_str})")
        else:
            logger.warning(f"No events found for tomorrow ({tomorrow_str})")
        
        # Fetch day after tomorrow's events
        day_after_tomorrow = today + timedelta(days=2)
        day_after_tomorrow_str = day_after_tomorrow.strftime("%Y-%m-%d")
        events_data_day_after = self._get_api("events", {
            "sport": "NBA", 
            "date": day_after_tomorrow_str,
            "lineups": "true"
        })
        if events_data_day_after and events_data_day_after.get("events"):
            all_events.extend(events_data_day_after["events"])
            logger.info(f"Found {len(events_data_day_after['events'])} events for day after tomorrow ({day_after_tomorrow_str})")
        else:
            logger.warning(f"No events found for day after tomorrow ({day_after_tomorrow_str})")
        
        if not all_events:
            logger.warning("No events found for any of the three days")
            return
        
        events_list = all_events
        event_ids = [str(e["id"]) for e in events_list]
        event_ids_str = ":".join(event_ids)

        # Cache events and sync team records + game venues
        db = SessionLocal()
        try:
            for e in events_list:
                home_abbr = e.get("home")
                away_abbr = e.get("visitor")
                event_dt = self._parse_event_datetime(e)
                participants = e.get("participants", [])
                venue = e.get("venue", {})
                
                # Use abbreviation mapping to find full team names
                home_name = self.NBA_TEAMS.get(home_abbr)
                away_name = self.NBA_TEAMS.get(away_abbr)
                
                # Find teams in our DB using full names
                home_team = db.query(Team).filter(Team.name == home_name).first() if home_name else None
                away_team = db.query(Team).filter(Team.name == away_name).first() if away_name else None
                
                # Fallback: try ILIKE if exact match fails
                if not home_team and home_name:
                    home_team = db.query(Team).filter(Team.name.ilike(f"%{home_name.split()[-1]}%")).first()
                if not away_team and away_name:
                    away_team = db.query(Team).filter(Team.name.ilike(f"%{away_name.split()[-1]}%")).first()
                
                # Update team records from API data
                for participant in participants:
                    team_record = participant.get("team", {}).get("record", {})
                    team_abbr = participant.get("id")
                    if team_record:
                        wins = team_record.get("W", 0)
                        losses = team_record.get("L", 0)
                        record_str = f"{wins}-{losses}"
                        
                        team_name = self.NBA_TEAMS.get(team_abbr)
                        team = db.query(Team).filter(Team.name == team_name).first() if team_name else None
                        if team and team.current_record != record_str:
                            team.current_record = record_str
                            logger.info(f"Updated {team.name} record to {record_str}")
                
                if home_team and away_team:
                    game = self._find_existing_scoreboard_game(
                        db,
                        home_team.id,
                        away_team.id,
                        event_dt,
                    )
                    
                    # Update game venue if available
                    if game and venue.get("name"):
                        venue_str = f"{venue.get('name')}, {venue.get('city', '')}"
                        if game.venue != venue_str:
                            game.venue = venue_str
                            logger.info(f"Updated venue for {home_team.name} game: {venue_str}")
                    
                    self.events_cache[e["id"]] = {
                        "home": home_team.name,
                        "away": away_team.name,
                        "home_abbr": home_abbr,
                        "away_abbr": away_abbr,
                        "game_id": game.id if game else None
                    }
                    if not game:
                        logger.warning(
                            f"Skipping BettingPros event {e.get('id')} ({away_name} @ {home_name}) - no matching scoreboard game"
                        )
                else:
                    # Log which teams failed to match
                    if not home_team:
                        logger.warning(f"Team not found for home abbreviation: {home_abbr} (mapped to: {home_name})")
                    if not away_team:
                        logger.warning(f"Team not found for away abbreviation: {away_abbr} (mapped to: {away_name})")
                    # Still cache the event with full names for save_odds to work
                    if home_name and away_name:
                        self.events_cache[e["id"]] = {
                            "home": home_name,
                            "away": away_name,
                            "home_abbr": home_abbr,
                            "away_abbr": away_abbr,
                            "game_id": None
                        }
            
            db.commit()
        finally:
            db.close()

        # 2. Scrape Game Lines - accumulate all markets per game before saving
        # Dict keyed by event_id -> accumulated odds data
        accumulated_odds: Dict[str, Dict] = {}

        for market_id, market_name in self.game_markets.items():
            logger.info(f"Syncing {market_name} market...")
            offers_data = self._get_api("offers", {
                "sport": "NBA",
                "market_id": market_id,
                "event_id": event_ids_str,
                "live": "false"
            })
            if offers_data and offers_data.get("offers"):
                for offer in offers_data["offers"]:
                    self._accumulate_game_offer(offer, market_id, accumulated_odds)

        # Save accumulated odds - one row per game with all markets
        for event_id, odds_data in accumulated_odds.items():
            self.save_odds(odds_data)

        # 3. Scrape Player Props
        for market_id, market_name in self.prop_markets.items():
            logger.info(f"Syncing {market_name} player props...")
            offers_data = self._get_api("offers", {
                "sport": "NBA",
                "market_id": market_id,
                "event_id": event_ids_str,
                "live": "false"
            })
            if offers_data and offers_data.get("offers"):
                for offer in offers_data["offers"]:
                    self._process_player_offer(offer, market_id)

    def _accumulate_game_offer(self, offer: Dict, market_id: int, accumulated: Dict):
        event_id = offer.get("event_id")
        event_info = self.events_cache.get(event_id)
        if not event_info: return
        if not event_info.get("game_id"): return

        # Initialize accumulated entry for this event if not exists
        if event_id not in accumulated:
            accumulated[event_id] = {
                "home_team": event_info["home"],
                "away_team": event_info["away"],
                "event_id": event_id,
                "game_id": event_info["game_id"],
                "bookmaker": "BettingPros"
            }

        odds_data = accumulated[event_id]
        market_name = self.game_markets[market_id]

        # Pre-compute home team name and abbreviation for consistent matching
        home_team_name = event_info["home"].lower()
        home_abbr = event_info.get("home_abbr", "").lower()

        selections = offer.get("selections", [])
        for sel in selections:
            sel_label = sel.get("label", "").lower()
            books = sel.get("books", [])
            # Prioritize FanDuel (10), then Consensus (0)
            fd_book = next((b for b in books if b.get("id") == 10), None)
            target_book = fd_book if fd_book else next((b for b in books if b.get("id") == 0), None)

            if target_book and target_book.get("lines"):
                line_data = target_book["lines"][0]
                val = line_data.get("line")
                cost = line_data.get("cost")

                if market_name == "moneyline":
                    # Check if selection label matches home team (partial match)
                    # Partial matching - check if selection is contained in team name or vice versa
                    is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                              sel_label == home_abbr or sel_label == home_team_name)
                    
                    if is_home:
                        odds_data["home_moneyline"] = cost
                    else:
                        odds_data["away_moneyline"] = cost
                elif market_name == "spread":
                    if "over" not in sel_label and "under" not in sel_label:
                        # Partial matching - check if selection is contained in team name or vice versa
                        is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                                  sel_label == home_abbr or sel_label == home_team_name)
                        
                        if is_home:
                            odds_data["home_spread"] = val
                            odds_data["home_spread_price"] = cost
                        else:
                            odds_data["away_spread"] = val
                            odds_data["away_spread_price"] = cost
                elif market_name == "total":
                    if "over" in sel_label:
                        odds_data["total_points"] = val
                        odds_data["over_price"] = cost
                    elif "under" in sel_label:
                        if "total_points" not in odds_data and val:
                            odds_data["total_points"] = val
                        odds_data["under_price"] = cost
                
                # Additional Game Props
                elif market_name == "team_total_home":
                    if "over" in sel_label:
                        odds_data["home_team_total"] = val
                        odds_data["home_team_total_over"] = cost
                    elif "under" in sel_label:
                        if "home_team_total" not in odds_data and val:
                            odds_data["home_team_total"] = val
                        odds_data["home_team_total_under"] = cost
                
                elif market_name == "team_total_away":
                    if "over" in sel_label:
                        odds_data["away_team_total"] = val
                        odds_data["away_team_total_over"] = cost
                    elif "under" in sel_label:
                        if "away_team_total" not in odds_data and val:
                            odds_data["away_team_total"] = val
                        odds_data["away_team_total_under"] = cost
                
                elif market_name == "first_half_spread":
                    if "over" not in sel_label and "under" not in sel_label:
                        is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                                  sel_label == home_abbr or sel_label == home_team_name)
                        if is_home:
                            odds_data["first_half_home_spread"] = val
                            odds_data["first_half_home_spread_price"] = cost
                        else:
                            odds_data["first_half_away_spread"] = val
                            odds_data["first_half_away_spread_price"] = cost
                
                elif market_name == "first_half_total":
                    if "over" in sel_label:
                        odds_data["first_half_total"] = val
                        odds_data["first_half_over"] = cost
                    elif "under" in sel_label:
                        if "first_half_total" not in odds_data and val:
                            odds_data["first_half_total"] = val
                        odds_data["first_half_under"] = cost
                
                elif market_name == "first_quarter_spread":
                    if "over" not in sel_label and "under" not in sel_label:
                        is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                                  sel_label == home_abbr or sel_label == home_team_name)
                        if is_home:
                            odds_data["first_quarter_home_spread"] = val
                            odds_data["first_quarter_home_spread_price"] = cost
                        else:
                            odds_data["first_quarter_away_spread"] = val
                            odds_data["first_quarter_away_spread_price"] = cost
                
                elif market_name == "first_quarter_total":
                    if "over" in sel_label:
                        odds_data["first_quarter_total"] = val
                        odds_data["first_quarter_over"] = cost
                    elif "under" in sel_label:
                        if "first_quarter_total" not in odds_data and val:
                            odds_data["first_quarter_total"] = val
                        odds_data["first_quarter_under"] = cost
                
                elif market_name == "first_half_moneyline":
                    is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                              sel_label == home_abbr or sel_label == home_team_name)
                    if is_home:
                        odds_data["first_half_home_moneyline"] = cost
                    else:
                        odds_data["first_half_away_moneyline"] = cost
                
                elif market_name == "first_quarter_moneyline":
                    is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                              sel_label == home_abbr or sel_label == home_team_name)
                    if is_home:
                        odds_data["first_quarter_home_moneyline"] = cost
                    else:
                        odds_data["first_quarter_away_moneyline"] = cost
                
                # Advanced Game Props
                elif market_name == "win_margin_home":
                    odds_data["home_win_margin"] = val
                    odds_data["home_win_margin_price"] = cost
                
                elif market_name == "win_margin_away":
                    odds_data["away_win_margin"] = val
                    odds_data["away_win_margin_price"] = cost
                
                elif market_name == "race_to_10_home":
                    odds_data["race_to_10_home"] = cost
                
                elif market_name == "race_to_10_away":
                    odds_data["race_to_10_away"] = cost
                
                elif market_name == "race_to_20_home":
                    odds_data["race_to_20_home"] = cost
                
                elif market_name == "race_to_20_away":
                    odds_data["race_to_20_away"] = cost
                
                elif market_name == "highest_scoring_quarter":
                    if "1st" in sel_label:
                        odds_data["highest_scoring_quarter_1st"] = cost
                    elif "2nd" in sel_label:
                        odds_data["highest_scoring_quarter_2nd"] = cost
                    elif "3rd" in sel_label:
                        odds_data["highest_scoring_quarter_3rd"] = cost
                    elif "4th" in sel_label:
                        odds_data["highest_scoring_quarter_4th"] = cost
                
                elif market_name == "both_teams_score_100":
                    if "yes" in sel_label:
                        odds_data["both_teams_score_100_yes"] = cost
                    elif "no" in sel_label:
                        odds_data["both_teams_score_100_no"] = cost
                
                elif market_name == "overtime_yes_no":
                    if "yes" in sel_label:
                        odds_data["overtime_yes"] = cost
                    elif "no" in sel_label:
                        odds_data["overtime_no"] = cost
                
                elif market_name == "double_result":
                    # Format: "Home/Home", "Home/Away", "Away/Home", "Away/Away"
                    if "home/home" in sel_label:
                        odds_data["double_result_home_home"] = cost
                    elif "home/away" in sel_label:
                        odds_data["double_result_home_away"] = cost
                    elif "away/home" in sel_label:
                        odds_data["double_result_away_home"] = cost
                    elif "away/away" in sel_label:
                        odds_data["double_result_away_away"] = cost
                
                elif market_name == "total_points_odd_even":
                    if "odd" in sel_label:
                        odds_data["total_points_odd"] = cost
                    elif "even" in sel_label:
                        odds_data["total_points_even"] = cost
                
                elif market_name == "team_total_odd_even_home":
                    if "odd" in sel_label:
                        odds_data["home_team_total_odd"] = cost
                    elif "even" in sel_label:
                        odds_data["home_team_total_even"] = cost

    def _process_player_offer(self, offer: Dict, market_id: int):
        event_id = offer.get("event_id")
        event_info = self.events_cache.get(event_id)
        if not event_info: return
        game_id = event_info.get("game_id")
        if not game_id:
            return
        
        participants = offer.get("participants", [])
        if not participants: return
        
        player = participants[0].get("player")
        if not player: return
        
        full_name = f"{player['first_name']} {player['last_name']}"
        prop_type = self.prop_markets[market_id]
        selections = offer.get("selections", [])
        
        # Extract team information
        player_team_abbr = player.get("team")
        player_team_name = None
        if player_team_abbr:
            player_team_name = self.NBA_TEAMS.get(player_team_abbr)
        
        # We need both Over and Under lines
        over_odds = 0
        under_odds = 0
        line = 0.0
        
        for sel in selections:
            sel_label = sel.get("selection", "").lower() # 'over' or 'under'
            books = sel.get("books", [])
            fd_book = next((b for b in books if b.get("id") == 10), None)
            target_book = fd_book if fd_book else next((b for b in books if b.get("id") == 0), None)
            
            if target_book and target_book.get("lines"):
                line_data = target_book["lines"][0]
                line = line_data.get("line")
                cost = line_data.get("cost")
                # Convert decimal odds to American odds
                american_odds = decimal_to_american(cost)
                if sel_label == "over": over_odds = american_odds
                else: under_odds = american_odds
                
                # Debug logging for extreme odds
                if cost > 50:  # Log any decimal odds over 50 as they're clearly wrong for sports betting
                    logger.warning(f"Suspicious high decimal odds: {cost} (decimal) -> {american_odds} (American) for {full_name} {prop_type} {sel_label}")
                    # For suspiciously high decimal odds, default to more realistic values
                    if cost > 100:
                        american_odds = -110  # Default to -110 for clearly corrupted data
        
        if line > 0:
            # Determine sportsbook name from target_book
            sportsbook_name = "Consensus"  # Default fallback
            if target_book:
                book_id = target_book.get("id")
                if book_id == 10:
                    sportsbook_name = "FanDuel"
                elif book_id == 0:
                    sportsbook_name = "Consensus"
                elif book_id == 2:
                    sportsbook_name = "DraftKings"
                elif book_id == 7:
                    sportsbook_name = "BetMGM"
                elif book_id == 20:
                    sportsbook_name = "Caesars"
                else:
                    sportsbook_name = f"Book_{book_id}"
            
            # Use player's team if available, otherwise fallback to home team (legacy behavior)
            target_team = player_team_name if player_team_name else event_info["home"]
            self.save_player_prop(full_name, prop_type, line, over_odds, under_odds, target_team, sportsbook_name, game_id=game_id)

    def save_odds(self, data: Dict):
        db = SessionLocal()
        try:
            game_id = data.get("game_id")
            if not game_id:
                logger.warning(f"Skipping odds save for event {data.get('event_id')} - no matched scoreboard game_id")
                return

            game = db.query(Game).filter(Game.id == game_id).first()
            if not game:
                logger.warning(f"Skipping odds save for event {data.get('event_id')} - game_id {game_id} not found")
                return
            
            # Determine spread_points: prefer home_spread, derive from away_spread if missing
            spread_pts = data.get("home_spread")
            if spread_pts is None and data.get("away_spread") is not None:
                spread_pts = -data["away_spread"]

            # Separate standard fields from additional props
            standard_fields = {
                "home_team", "away_team", "bookmaker", 
                "home_moneyline", "away_moneyline", 
                "home_spread", "away_spread", "home_spread_price", "away_spread_price",
                "total_points", "over_price", "under_price"
            }
            
            additional_props = {k: v for k, v in data.items() if k not in standard_fields}

            odds_entry = BettingOdds(
                game_id=game.id,
                bookmaker=data.get("bookmaker", "BettingPros"),
                home_moneyline=data.get("home_moneyline"),
                away_moneyline=data.get("away_moneyline"),
                spread_points=spread_pts,
                home_spread_price=data.get("home_spread_price"),
                away_spread_price=data.get("away_spread_price"),
                total_points=data.get("total_points"),
                over_price=data.get("over_price"),
                under_price=data.get("under_price"),
                additional_props=additional_props,
                timestamp=datetime.utcnow()
            )
            db.add(odds_entry)
            db.commit()
            logger.info(f"Saved odds for game_id {game.id}")
        except Exception as e:
            logger.error(f"Error saving odds: {e}")
            db.rollback()
        finally:
            db.close()

    def save_player_prop(self, player_name: str, prop_type: str, line: float, over_odds: int, under_odds: int, team_name: str, sportsbook: str = "Consensus", game_id: Optional[int] = None):
        db = SessionLocal()
        try:
            game = db.query(Game).filter(Game.id == game_id).first() if game_id else None
            if not game:
                logger.warning(f"Skipping prop save for {player_name} ({prop_type}) - no matched scoreboard game_id")
                return

            player = db.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
            
            # Find the team for this player
            team = db.query(Team).filter(Team.name.ilike(f"%{team_name}%")).first()
            
            if not player:
                player = Player(name=player_name, sport="NBA", active_status=True, team_id=team.id if team else None)
                db.add(player)
                db.commit()
                db.refresh(player)
            elif not player.team_id and team:
                # Update team_id if missing
                player.team_id = team.id
                db.commit()
                db.refresh(player)

            prop = db.query(PlayerProps).filter(
                PlayerProps.player_id == player.id,
                PlayerProps.game_id == game.id,
                PlayerProps.prop_type == prop_type,
                PlayerProps.line == line
            ).first()

            if not prop:
                prop = PlayerProps(
                    player_id=player.id,
                    game_id=game.id,
                    prop_type=prop_type,
                    line=line,
                    over_odds=over_odds,
                    under_odds=under_odds,
                    sportsbook=sportsbook
                )
                db.add(prop)
            else:
                prop.over_odds = over_odds
                prop.under_odds = under_odds
                prop.sportsbook = sportsbook
            
            prop.timestamp = datetime.utcnow()
            db.commit()
            logger.info(f"Saved {prop_type} prop for {player_name}")
        except Exception as e:
            logger.error(f"Error saving prop: {e}")
            db.rollback()
        finally:
            db.close()

    async def scrape_prop_analyzer(self):
        """
        Fetches pre-analyzed prop data from the /props endpoint.
        This provides star ratings, EV calculations, and performance stats.
        """
        logger.info("Fetching BettingPros Prop Analyzer data...")
        
        # Fetch top props sorted by edge differential
        props_data = self._get_api("props", {
            "sport": "NBA",
            "limit": 200,
            "sort": "diff",
            "sort_direction": "desc"
        })
        
        if not props_data or not props_data.get("props"):
            logger.warning("No props data from analyzer endpoint")
            return
        
        db = SessionLocal()
        try:
            updated_count = 0
            created_count = 0
            
            for prop in props_data["props"]:
                # Extract player info
                participant = prop.get("participant", {})
                player_info = participant.get("player", {})
                player_name = f"{player_info.get('first_name', '')} {player_info.get('last_name', '')}".strip()
                if not player_name:
                    continue
                
                # Extract team and event info
                team_abbr = player_info.get("team")
                event_id = str(prop.get("event_id"))
                
                # Find game for this prop
                game_id = None
                
                # Strategy 1: Check events cache if we have it
                if event_id in self.events_cache:
                    game_id = self.events_cache[event_id].get("game_id")

                # Scoreboard-first policy: do not attach analyzer props to inferred team/date games.
                if not game_id:
                    continue

                # Extract projection and analyzer data
                projection = prop.get("projection", {})
                over_data = prop.get("over", {})
                under_data = prop.get("under", {})
                performance = prop.get("performance", {})
                
                # Get the best available bet rating (from projection or over/under)
                star_rating = projection.get("bet_rating") or over_data.get("bet_rating") or under_data.get("bet_rating")
                
                # Get EV from the recommended side
                recommended_side = projection.get("recommended_side", "").lower()
                if recommended_side == "over":
                    bp_ev = over_data.get("expected_value")
                    line = over_data.get("line")
                    over_odds = over_data.get("odds")
                    under_odds = under_data.get("odds")
                else:
                    bp_ev = under_data.get("expected_value")
                    line = under_data.get("line")
                    over_odds = over_data.get("odds")
                    under_odds = under_data.get("odds")
                
                # Get performance percentage from last_15
                last_15 = performance.get("last_15", {})
                if last_15:
                    total = (last_15.get("over", 0) or 0) + (last_15.get("under", 0) or 0)
                    if total > 0:
                        if recommended_side == "over":
                            perf_pct = (last_15.get("over", 0) or 0) / total
                        else:
                            perf_pct = (last_15.get("under", 0) or 0) / total
                    else:
                        perf_pct = None
                else:
                    perf_pct = None
                
                # Map market_id to prop_type
                market_id = prop.get("market_id")
                # Extended market ID mapping
                market_map = {
                    156: "points",
                    159: "rebounds",
                    157: "assists",
                    158: "threes",
                    161: "steals",
                    162: "blocks",
                    335: "pts+ast",
                    336: "pts+reb",
                    337: "reb+ast",
                    338: "pts+reb+ast",
                    147: "double_double",
                    160: "triple_double",
                    152: "turnovers",
                    142: "fantasy_score",
                    136: "minutes"
                }
                prop_type = market_map.get(market_id)
                if not prop_type or not line:
                    continue
                
                # Find player in DB
                player = db.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
                if not player:
                    # Create player if not exists
                    player = Player(name=player_name, sport="NBA", active_status=True)
                    db.add(player)
                    db.commit()
                    db.refresh(player)
                
                # Find or create prop
                existing_prop = db.query(PlayerProps).filter(
                    PlayerProps.player_id == player.id,
                    PlayerProps.prop_type == prop_type,
                    PlayerProps.line == line
                ).first()
                
                if existing_prop:
                    # Update with analyzer data
                    existing_prop.game_id = game_id
                    existing_prop.star_rating = star_rating
                    existing_prop.bp_ev = bp_ev
                    existing_prop.performance_pct = perf_pct
                    existing_prop.recommended_side = recommended_side
                    existing_prop.over_odds = over_odds
                    existing_prop.under_odds = under_odds
                    updated_count += 1
                else:
                    # Create new prop with analyzer data
                    new_prop = PlayerProps(
                        player_id=player.id,
                        game_id=game_id,  # Include game_id if we found it
                        prop_type=prop_type,
                        line=line,
                        over_odds=over_odds or 0,
                        under_odds=under_odds or 0,
                        star_rating=star_rating,
                        bp_ev=bp_ev,
                        performance_pct=perf_pct,
                        recommended_side=recommended_side
                    )
                    db.add(new_prop)
                    created_count += 1
            
            db.commit()
            logger.info(f"Prop Analyzer: Updated {updated_count}, Created {created_count} props with analyzer data")
        except Exception as e:
            logger.error(f"Error updating prop analyzer data: {e}")
            db.rollback()
        finally:
            db.close()


async def main():
    scraper = BettingProsScraper(headless=True)
    
    # Scrape specific players as requested
    logger.info("Scraping specific player props...")
    await scraper.scrape_player_props_by_name("LeBron James")
    await scraper.scrape_player_props_by_name("Austin Reaves")
    await scraper.scrape_player_props_by_name("Luka Doncic")
    
    # Also run the regular scraper
    await scraper.scrape_nba_data()
    await scraper.scrape_prop_analyzer()

if __name__ == "__main__":
    asyncio.run(main())
