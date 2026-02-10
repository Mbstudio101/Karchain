import asyncio
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Optional

from .base_scraper import BaseScraper
from app.database import SessionLocal
from app.models import Team, Game, BettingOdds, Player, PlayerProps

logger = logging.getLogger(__name__)

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
            129: "spread"
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

    def _get_api(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API Request failed for {endpoint}: {e}")
            return None

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
                    # Look for games from today and tomorrow
                    from datetime import timedelta
                    today = datetime.utcnow().date()
                    tomorrow = today + timedelta(days=1)
                    
                    game = db.query(Game).filter(
                        Game.home_team_id == home_team.id,
                        Game.away_team_id == away_team.id,
                        Game.game_date >= today
                    ).first()
                    
                    # Update game venue if available
                    if game and venue.get("name"):
                        venue_str = f"{venue.get('name')}, {venue.get('city', '')}"
                        if game.venue != venue_str:
                            game.venue = venue_str
                            logger.info(f"Updated venue for {home_team.name} game: {venue_str}")
                    
                    self.events_cache[e["id"]] = {
                        "home": home_team.name,
                        "away": away_team.name,
                        "game_id": game.id if game else None
                    }
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

        # Initialize accumulated entry for this event if not exists
        if event_id not in accumulated:
            accumulated[event_id] = {
                "home_team": event_info["home"],
                "away_team": event_info["away"],
                "bookmaker": "BettingPros"
            }

        odds_data = accumulated[event_id]
        market_name = self.game_markets[market_id]

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
                    home_team_name = event_info["home"].lower()
                    home_abbr = event_info.get("home_abbr", "").lower()
                    
                    # Partial matching - check if selection is contained in team name or vice versa
                    is_home = (sel_label in home_team_name or home_team_name in sel_label or 
                              sel_label == home_abbr or sel_label == home_team_name)
                    
                    if is_home:
                        odds_data["home_moneyline"] = cost
                    else:
                        odds_data["away_moneyline"] = cost
                elif market_name == "spread":
                    if "over" not in sel_label and "under" not in sel_label:
                        # Check if selection label matches home team (partial match)
                        home_team_name = event_info["home"].lower()
                        home_abbr = event_info.get("home_abbr", "").lower()
                        
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

    def _process_player_offer(self, offer: Dict, market_id: int):
        event_id = offer.get("event_id")
        event_info = self.events_cache.get(event_id)
        if not event_info: return
        
        participants = offer.get("participants", [])
        if not participants: return
        
        player = participants[0].get("player")
        if not player: return
        
        full_name = f"{player['first_name']} {player['last_name']}"
        prop_type = self.prop_markets[market_id]
        selections = offer.get("selections", [])
        
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
                if sel_label == "over": over_odds = cost
                else: under_odds = cost
        
        if line > 0:
            self.save_player_prop(full_name, prop_type, line, over_odds, under_odds, event_info["home"])

    def save_odds(self, data: Dict):
        db = SessionLocal()
        try:
            home_team = db.query(Team).filter(Team.name.ilike(f"%{data['home_team']}%")).first()
            away_team = db.query(Team).filter(Team.name.ilike(f"%{data['away_team']}%")).first()
            if not home_team or not away_team: return
            
            # Look for games from today and tomorrow
            from datetime import timedelta
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            
            # Get the MOST RECENT game (highest ID) to handle duplicate entries
            game = db.query(Game).filter(
                Game.home_team_id == home_team.id, 
                Game.away_team_id == away_team.id, 
                Game.game_date >= today
            ).order_by(Game.id.desc()).first()
            if not game: return
            
            # Determine spread_points: prefer home_spread, derive from away_spread if missing
            spread_pts = data.get("home_spread")
            if spread_pts is None and data.get("away_spread") is not None:
                spread_pts = -data["away_spread"]

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
                timestamp=datetime.utcnow()
            )
            db.add(odds_entry)
            db.commit()
            logger.info(f"Saved odds for {home_team.name} vs {away_team.name}")
        except Exception as e:
            logger.error(f"Error saving odds: {e}")
            db.rollback()
        finally:
            db.close()

    def save_player_prop(self, player_name: str, prop_type: str, line: float, over_odds: int, under_odds: int, home_team_name: str):
        db = SessionLocal()
        try:
            # Look for games from today and tomorrow
            from datetime import timedelta
            today = datetime.utcnow().date()
            tomorrow = today + timedelta(days=1)
            
            game = db.query(Game).join(Team, Game.home_team_id == Team.id).filter(
                Team.name.ilike(f"%{home_team_name}%"),
                Game.game_date >= today
            ).first()
            if not game: return

            player = db.query(Player).filter(Player.name.ilike(f"%{player_name}%")).first()
            if not player:
                player = Player(name=player_name, sport="NBA", active_status=True)
                db.add(player)
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
                    under_odds=under_odds
                )
                db.add(prop)
            else:
                prop.over_odds = over_odds
                prop.under_odds = under_odds
            
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
                    151: "pts+reb",
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
    await scraper.scrape_nba_data()
    await scraper.scrape_prop_analyzer()

if __name__ == "__main__":
    asyncio.run(main())

