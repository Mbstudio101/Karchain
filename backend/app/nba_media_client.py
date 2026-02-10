"""
NBA Media Client for fetching player headshots and team logos
Uses official NBA CDN and ESPN endpoints for authentic media assets
"""

import requests
import logging
from typing import Optional, Dict
import os
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class NBAMediaClient:
    """Client for fetching NBA player headshots and team logos from official sources"""
    
    def __init__(self):
        # Official NBA CDN endpoints
        self.nba_headshot_base = "https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190"
        self.nba_fallback_headshot = "https://cdn.nba.com/headshots/nba/latest/260x190/fallback.png"
        
        # ESPN team logos (reliable and high quality)
        self.espn_logo_base = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500"
        self.espn_logo_fallback = "https://a.espncdn.com/combiner/i?img=/i/teamlogos/nba/500/scoreboard.png&h=200&w=200"
        
        # Cache for media URLs to avoid repeated requests
        self._headshot_cache: Dict[str, str] = {}
        self._logo_cache: Dict[str, str] = {}
        self._cache_expiry = timedelta(hours=24)
        self._cache_timestamp: Dict[str, datetime] = {}
        
        # Team abbreviation mapping for consistent logo URLs
        self.team_abbreviations = {
            'Atlanta Hawks': 'atl',
            'Brooklyn Nets': 'bkn',
            'Boston Celtics': 'bos',
            'Charlotte Hornets': 'cha',
            'Chicago Bulls': 'chi',
            'Cleveland Cavaliers': 'cle',
            'Dallas Mavericks': 'dal',
            'Denver Nuggets': 'den',
            'Detroit Pistons': 'det',
            'Golden State Warriors': 'gsw',
            'Houston Rockets': 'hou',
            'Indiana Pacers': 'ind',
            'Los Angeles Clippers': 'lac',
            'Los Angeles Lakers': 'lal',
            'Memphis Grizzlies': 'mem',
            'Miami Heat': 'mia',
            'Milwaukee Bucks': 'mil',
            'Minnesota Timberwolves': 'min',
            'New Orleans Pelicans': 'nop',
            'New York Knicks': 'nyk',
            'Oklahoma City Thunder': 'okc',
            'Orlando Magic': 'orl',
            'Philadelphia 76ers': 'phi',
            'Phoenix Suns': 'phx',
            'Portland Trail Blazers': 'por',
            'Sacramento Kings': 'sac',
            'San Antonio Spurs': 'sas',
            'Toronto Raptors': 'tor',
            'Utah Jazz': 'uta',
            'Washington Wizards': 'was'
        }
        
        # Alternative team name mappings
        self.alternative_names = {
            'LA Clippers': 'Los Angeles Clippers',
            'LA Lakers': 'Los Angeles Lakers',
            'NY Knicks': 'New York Knicks',
            'NO Pelicans': 'New Orleans Pelicans',
            'OKC Thunder': 'Oklahoma City Thunder',
            'SA Spurs': 'San Antonio Spurs',
            'GS Warriors': 'Golden State Warriors'
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_timestamp:
            return False
        
        age = datetime.now() - self._cache_timestamp[cache_key]
        return age < self._cache_expiry
    
    def _get_team_abbreviation(self, team_name: str) -> str:
        """Get standardized team abbreviation"""
        # Handle alternative names
        if team_name in self.alternative_names:
            team_name = self.alternative_names[team_name]
        
        # Try exact match first
        if team_name in self.team_abbreviations:
            return self.team_abbreviations[team_name]
        
        # Try partial match
        for full_name, abbrev in self.team_abbreviations.items():
            if team_name.lower() in full_name.lower() or full_name.lower() in team_name.lower():
                return abbrev
        
        # Fallback: create abbreviation from name
        words = team_name.split()
        if len(words) >= 2:
            return ''.join(word[0].lower() for word in words[:2])
        return team_name[:3].lower()
    
    def get_player_headshot(self, player_name: str, player_id: Optional[str] = None) -> str:
        """
        Get NBA player headshot URL
        
        Args:
            player_name: Full player name (e.g., "LeBron James")
            player_id: NBA player ID (optional, improves accuracy)
        
        Returns:
            URL to player headshot image
        """
        cache_key = f"headshot_{player_name}_{player_id}"
        
        # Check cache first
        if cache_key in self._headshot_cache and self._is_cache_valid(cache_key):
            return self._headshot_cache[cache_key]
        
        try:
            # If we have player_id, use it directly for NBA CDN
            if player_id:
                headshot_url = f"{self.nba_headshot_base}/{player_id}.png"
                
                # Test if the headshot exists
                response = requests.head(headshot_url, timeout=5)
                if response.status_code == 200:
                    self._headshot_cache[cache_key] = headshot_url
                    self._cache_timestamp[cache_key] = datetime.now()
                    return headshot_url
            
            # Try to find player ID from name using NBA API
            if not player_id:
                try:
                    from app.nba_api_client import get_nba_client
                    nba_client = get_nba_client()
                    
                    # Search for player by name
                    players = nba_client.search_players(player_name)
                    if players and len(players) > 0:
                        player_id = str(players[0].get('id', ''))
                        if player_id:
                            headshot_url = f"{self.nba_headshot_base}/{player_id}.png"
                            response = requests.head(headshot_url, timeout=5)
                            if response.status_code == 200:
                                self._headshot_cache[cache_key] = headshot_url
                                self._cache_timestamp[cache_key] = datetime.now()
                                return headshot_url
                except Exception as e:
                    logger.warning(f"Failed to search NBA API for player {player_name}: {e}")
            
            # Fallback: Try ESPN headshots
            try:
                # ESPN uses a different format, try to construct URL
                espn_headshot = self._get_espn_headshot(player_name)
                if espn_headshot:
                    self._headshot_cache[cache_key] = espn_headshot
                    self._cache_timestamp[cache_key] = datetime.now()
                    return espn_headshot
            except Exception as e:
                logger.warning(f"Failed to get ESPN headshot for {player_name}: {e}")
            
            # Final fallback to NBA default
            self._headshot_cache[cache_key] = self.nba_fallback_headshot
            self._cache_timestamp[cache_key] = datetime.now()
            return self.nba_fallback_headshot
            
        except Exception as e:
            logger.error(f"Error getting headshot for {player_name}: {e}")
            return self.nba_fallback_headshot
    
    def _get_espn_headshot(self, player_name: str) -> Optional[str]:
        """Try to get headshot from ESPN"""
        # ESPN headshots are harder to predict, but we can try common formats
        # This is a simplified approach - in practice, you'd want to use ESPN's API
        return None
    
    def get_team_logo(self, team_name: str, size: int = 200) -> str:
        """
        Get NBA team logo URL
        
        Args:
            team_name: Full team name (e.g., "Los Angeles Lakers")
            size: Logo size in pixels (default: 200)
        
        Returns:
            URL to team logo image
        """
        cache_key = f"logo_{team_name}_{size}"
        
        # Check cache first
        if cache_key in self._logo_cache and self._is_cache_valid(cache_key):
            return self._logo_cache[cache_key]
        
        try:
            # Get team abbreviation
            team_abbrev = self._get_team_abbreviation(team_name)
            
            # Construct ESPN logo URL
            logo_url = f"{self.espn_logo_base}/{team_abbrev}.png&h={size}&w={size}"
            
            # Test if logo exists
            response = requests.head(logo_url, timeout=5)
            if response.status_code == 200:
                self._logo_cache[cache_key] = logo_url
                self._cache_timestamp[cache_key] = datetime.now()
                return logo_url
            
            # Fallback: Try NBA CDN
            nba_logo_url = f"https://cdn.nba.com/logos/nba/{team_abbrev}/primary/L/logo.svg"
            response = requests.head(nba_logo_url, timeout=5)
            if response.status_code == 200:
                self._logo_cache[cache_key] = nba_logo_url
                self._cache_timestamp[cache_key] = datetime.now()
                return nba_logo_url
            
            # Final fallback to ESPN generic logo
            fallback_url = f"{self.espn_logo_fallback}&h={size}&w={size}"
            self._logo_cache[cache_key] = fallback_url
            self._cache_timestamp[cache_key] = datetime.now()
            return fallback_url
            
        except Exception as e:
            logger.error(f"Error getting logo for {team_name}: {e}")
            return self.espn_logo_fallback
    
    def get_player_headshot_with_fallback(self, player_name: str, player_id: Optional[str] = None, 
                                        fallback_url: Optional[str] = None) -> Dict[str, str]:
        """
        Get player headshot with multiple fallback options
        
        Returns:
            Dict with 'url' and 'source' keys
        """
        primary_url = self.get_player_headshot(player_name, player_id)
        
        result = {
            'url': primary_url,
            'source': 'nba_cdn' if 'ak-static.cms.nba.com' in primary_url else 'espn',
            'is_fallback': primary_url == self.nba_fallback_headshot
        }
        
        # If primary failed and custom fallback provided, use it
        if result['is_fallback'] and fallback_url:
            result['url'] = fallback_url
            result['source'] = 'custom_fallback'
        
        return result
    
    def get_team_logo_with_fallback(self, team_name: str, size: int = 200, 
                                    fallback_url: Optional[str] = None) -> Dict[str, str]:
        """
        Get team logo with multiple fallback options
        
        Returns:
            Dict with 'url' and 'source' keys
        """
        primary_url = self.get_team_logo(team_name, size)
        
        result = {
            'url': primary_url,
            'source': 'espn' if 'espncdn.com' in primary_url else 'nba_cdn',
            'is_fallback': primary_url == self.espn_logo_fallback
        }
        
        # If primary failed and custom fallback provided, use it
        if result['is_fallback'] and fallback_url:
            result['url'] = fallback_url
            result['source'] = 'custom_fallback'
        
        return result
    
    def clear_cache(self):
        """Clear all cached media URLs"""
        self._headshot_cache.clear()
        self._logo_cache.clear()
        self._cache_timestamp.clear()
        logger.info("NBA Media Client cache cleared")


# Global instance for easy access
_media_client = None

def get_nba_media_client() -> NBAMediaClient:
    """Get global NBA Media Client instance"""
    global _media_client
    if _media_client is None:
        _media_client = NBAMediaClient()
    return _media_client