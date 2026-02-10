"""
Enhanced NBA API Client with Caching, Retry Logic, and Circuit Breaker
Handles timeouts, 500 errors, and provides fallback data sources
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import json
import logging
from functools import wraps
import hashlib
import os
from threading import Lock
import pickle
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class CircuitBreaker:
    """Circuit breaker pattern to prevent cascading failures"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = Lock()
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self._lock:
                if self.state == "open":
                    if time.time() - self.last_failure_time > self.recovery_timeout:
                        self.state = "half-open"
                        logger.info(f"Circuit breaker for {func.__name__} moved to half-open state")
                    else:
                        logger.warning(f"Circuit breaker for {func.__name__} is open, skipping call")
                        raise Exception(f"Circuit breaker is open for {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                with self._lock:
                    if self.state == "half-open":
                        self.state = "closed"
                        self.failure_count = 0
                        logger.info(f"Circuit breaker for {func.__name__} closed successfully")
                return result
            except self.expected_exception as e:
                with self._lock:
                    self.failure_count += 1
                    self.last_failure_time = time.time()
                    if self.failure_count >= self.failure_threshold:
                        self.state = "open"
                        logger.error(f"Circuit breaker for {func.__name__} opened due to {self.failure_count} failures")
                raise e
        
        return wrapper

class EnhancedNBAApiClient:
    """Enhanced NBA API client with caching, retry logic, and circuit breakers"""
    
    def __init__(self, cache_ttl=3600, max_retries=3, retry_delay=1.0):
        self.base_url = "https://stats.nba.com"
        self.espn_base = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba"
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._cache_lock = Lock()
        
        # Enhanced headers to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'x-nba-stats-origin': 'stats',
            'x-nba-stats-token': 'true',
            'Referer': 'https://stats.nba.com/',
            'Origin': 'https://stats.nba.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Configure connection pooling and timeouts
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=10,
            max_retries=requests.adapters.Retry(
                total=2,
                backoff_factor=0.3,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def _get_cache_key(self, func_name, *args, **kwargs):
        """Generate a cache key from function name and arguments"""
        key_data = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, key):
        """Get value from cache"""
        with self._cache_lock:
            if key in self.cache:
                timestamp = self.cache_timestamps[key]
                if time.time() - timestamp < self.cache_ttl:
                    return self.cache[key]
                else:
                    # Expired, remove from cache
                    del self.cache[key]
                    del self.cache_timestamps[key]
            return None
    
    def _set_cache(self, key, value):
        """Set value in cache"""
        with self._cache_lock:
            self.cache[key] = value
            self.cache_timestamps[key] = time.time()
    
    def _make_request(self, url: str, params: Dict = None, timeout: int = 15) -> Optional[Dict]:
        """Make HTTP request with retry logic and error handling"""
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Attempt {attempt + 1} for {url}")
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                return response.json()
            
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error on attempt {attempt + 1} for {url}: {e}")
                if response.status_code in [500, 502, 503, 504] and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return None
            
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1} for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                continue
        
        logger.error(f"All retry attempts failed for {url}")
        return None
    
    def _cached_api_call(self, func_name, api_call_func, *args, **kwargs):
        """Wrapper for cached API calls"""
        cache_key = self._get_cache_key(func_name, *args, **kwargs)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result is not None:
            logger.debug(f"Cache hit for {func_name}")
            return cached_result
        
        result = api_call_func(*args, **kwargs)
        if result is not None:
            self._set_cache(cache_key, result)
        return result
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=300)
    def get_player_clutch_stats(self, player_id: str, season: str = "2024-25") -> Dict[str, float]:
        """Get real clutch time statistics with enhanced error handling"""
        def _fetch_clutch_stats(player_id: str, season: str):
            url = f"{self.base_url}/stats/leaguedashplayerclutch"
            params = {
                'Season': season,
                'SeasonType': 'Regular Season',
                'ClutchTime': 'Last 5 Minutes',
                'PointDiff': 5,
                'PerMode': 'PerGame'
            }
            
            data = self._make_request(url, params)
            if not data:
                logger.warning(f"Failed to fetch clutch stats for player {player_id}, using fallback")
                return self._get_fallback_clutch_stats()
            
            try:
                # Find player in clutch data
                for row in data['resultSets'][0]['rowSet']:
                    if str(row[0]) == player_id:
                        clutch_pts = float(row[8]) if row[8] else 0.0
                        clutch_fg_pct = float(row[11]) if row[11] else 0.0
                        clutch_efg_pct = float(row[12]) if row[12] else 0.0
                        clutch_usg_pct = float(row[20]) if row[20] else 0.0
                        
                        return {
                            'clutch_pts_per_game': clutch_pts,
                            'clutch_fg_percentage': clutch_fg_pct,
                            'clutch_efg_percentage': clutch_efg_pct,
                            'clutch_usage_percentage': clutch_usg_pct,
                            'clutch_rating': self._calculate_clutch_rating(clutch_pts, clutch_efg_pct, clutch_usg_pct),
                            'data_source': 'nba_api',
                            'last_updated': datetime.now().isoformat()
                        }
                
                logger.warning(f"No clutch data found for player {player_id}")
                return self._get_fallback_clutch_stats()
                
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing clutch stats for player {player_id}: {e}")
                return self._get_fallback_clutch_stats()
        
        return self._cached_api_call('get_player_clutch_stats', _fetch_clutch_stats, player_id, season)
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=300)
    def get_player_tracking_stats(self, player_id: str, season: str = "2024-25") -> Dict[str, float]:
        """Get player tracking stats with enhanced error handling"""
        def _fetch_tracking_stats(player_id: str, season: str):
            url = f"{self.base_url}/stats/leaguedashptstats"
            params = {
                'Season': season,
                'SeasonType': 'Regular Season',
                'PtMeasureType': 'SpeedDistance',
                'PerMode': 'PerGame'
            }
            
            data = self._make_request(url, params)
            if not data:
                logger.warning(f"Failed to fetch tracking stats for player {player_id}, using fallback")
                return self._get_fallback_tracking_stats()
            
            try:
                for row in data['resultSets'][0]['rowSet']:
                    if str(row[0]) == player_id:
                        avg_speed = float(row[7]) if row[7] else 0.0
                        distance = float(row[8]) if row[8] else 0.0
                        
                        return {
                            'avg_speed': avg_speed,
                            'distance_per_game': distance,
                            'speed_factor': min(avg_speed / 5.0, 1.0),
                            'distance_factor': min(distance / 3.0, 1.0),
                            'data_source': 'nba_api',
                            'last_updated': datetime.now().isoformat()
                        }
                
                logger.warning(f"No tracking data found for player {player_id}")
                return self._get_fallback_tracking_stats()
                
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing tracking stats for player {player_id}: {e}")
                return self._get_fallback_tracking_stats()
        
        return self._cached_api_call('get_player_tracking_stats', _fetch_tracking_stats, player_id, season)
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=300)
    def get_defensive_impact(self, player_id: str, season: str = "2024-25") -> Dict[str, float]:
        """Get defensive impact statistics"""
        def _fetch_defensive_stats(player_id: str, season: str):
            url = f"{self.base_url}/stats/leaguedashptdefend"
            params = {
                'Season': season,
                'SeasonType': 'Regular Season',
                'PtMeasureType': 'Defense Dashboard',
                'PerMode': 'PerGame'
            }
            
            data = self._make_request(url, params)
            if not data:
                logger.warning(f"Failed to fetch defensive stats for player {player_id}, using fallback")
                return self._get_fallback_defensive_stats()
            
            try:
                for row in data['resultSets'][0]['rowSet']:
                    if str(row[0]) == player_id:
                        dfg_pct = float(row[9]) if row[9] else 0.0  # DFG_PCT
                        dfgm = float(row[7]) if row[7] else 0.0  # DFGM
                        dfga = float(row[8]) if row[8] else 0.0  # DFGA
                        
                        return {
                            'defensive_fg_percentage': dfg_pct,
                            'defensive_fgm': dfgm,
                            'defensive_fga': dfga,
                            'defensive_impact': self._calculate_defensive_impact(dfg_pct, dfga),
                            'data_source': 'nba_api',
                            'last_updated': datetime.now().isoformat()
                        }
                
                logger.warning(f"No defensive data found for player {player_id}")
                return self._get_fallback_defensive_stats()
                
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing defensive stats for player {player_id}: {e}")
                return self._get_fallback_defensive_stats()
        
        return self._cached_api_call('get_defensive_impact', _fetch_defensive_stats, player_id, season)
    
    @CircuitBreaker(failure_threshold=3, recovery_timeout=300)
    def get_live_player_stats(self, player_id: str, season: str = "2024-25") -> Dict[str, float]:
        """Get current season player statistics"""
        def _fetch_live_stats(player_id: str, season: str):
            url = f"{self.base_url}/stats/playerdashboardbyyearoveryear"
            params = {
                'PlayerID': player_id,
                'Season': season,
                'SeasonType': 'Regular Season'
            }
            
            data = self._make_request(url, params)
            if not data:
                logger.warning(f"Failed to fetch live stats for player {player_id}, using fallback")
                return self._get_fallback_live_stats()
            
            try:
                # Get current season stats from first row
                if data['resultSets'] and len(data['resultSets']) > 0:
                    row = data['resultSets'][0]['rowSet'][0] if data['resultSets'][0]['rowSet'] else None
                    if row:
                        return {
                            'ppg': float(row[26]) if len(row) > 26 and row[26] else 0.0,  # PTS
                            'rpg': float(row[20]) if len(row) > 20 and row[20] else 0.0,  # REB
                            'apg': float(row[21]) if len(row) > 21 and row[21] else 0.0,  # AST
                            'fg_pct': float(row[11]) if len(row) > 11 and row[11] else 0.0,  # FG_PCT
                            'three_pct': float(row[14]) if len(row) > 14 and row[14] else 0.0,  # FG3_PCT
                            'minutes': float(row[8]) if len(row) > 8 and row[8] else 0.0,  # MIN
                            'games_played': int(row[6]) if len(row) > 6 and row[6] else 0,  # GP
                            'data_source': 'nba_api',
                            'last_updated': datetime.now().isoformat()
                        }
                
                logger.warning(f"No live stats found for player {player_id}")
                return self._get_fallback_live_stats()
                
            except (IndexError, ValueError) as e:
                logger.error(f"Error parsing live stats for player {player_id}: {e}")
                return self._get_fallback_live_stats()
        
        return self._cached_api_call('get_live_player_stats', _fetch_live_stats, player_id, season)
    
    # Fallback methods
    def _get_fallback_clutch_stats(self) -> Dict[str, float]:
        """Conservative fallback clutch statistics"""
        return {
            'clutch_pts_per_game': 2.5,
            'clutch_fg_percentage': 0.42,
            'clutch_efg_percentage': 0.47,
            'clutch_usage_percentage': 18.0,
            'clutch_rating': 0.65,
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fallback_tracking_stats(self) -> Dict[str, float]:
        """Conservative fallback tracking statistics"""
        return {
            'avg_speed': 4.2,
            'distance_per_game': 2.8,
            'speed_factor': 0.65,
            'distance_factor': 0.75,
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fallback_defensive_stats(self) -> Dict[str, float]:
        """Conservative fallback defensive statistics"""
        return {
            'defensive_fg_percentage': 0.45,
            'defensive_fgm': 2.0,
            'defensive_fga': 4.5,
            'defensive_impact': 0.55,
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_fallback_live_stats(self) -> Dict[str, float]:
        """Conservative fallback live statistics"""
        return {
            'ppg': 12.0,
            'rpg': 4.0,
            'apg': 3.0,
            'fg_pct': 0.45,
            'three_pct': 0.35,
            'minutes': 28.0,
            'games_played': 15,
            'data_source': 'fallback',
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_clutch_rating(self, pts: float, efg_pct: float, usg_pct: float) -> float:
        """Calculate composite clutch rating"""
        pts_score = min(pts / 5.0, 1.0)
        efg_score = efg_pct
        usg_score = min(usg_pct / 35.0, 1.0)
        return (pts_score * 0.4 + efg_score * 0.4 + usg_score * 0.2)
    
    def _calculate_defensive_impact(self, dfg_pct: float, dfga: float) -> float:
        """Calculate defensive impact score"""
        fg_impact = (0.45 - dfg_pct) / 0.45  # Lower is better
        volume_score = min(dfga / 10.0, 1.0)
        return max(0.0, (fg_impact * 0.7 + volume_score * 0.3))
    
    def search_players(self, player_name: str) -> List[Dict[str, Any]]:
        """Search for players by name (placeholder implementation)"""
        # This would typically integrate with NBA's player search API
        # For now, return empty list to avoid breaking existing code
        return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._cache_lock:
            return {
                'cache_size': len(self.cache),
                'cache_entries': list(self.cache.keys())[:10],  # First 10 keys
                'cache_hit_rate': 'Not implemented'  # Could be added with counters
            }


# Global instance for easy access
_enhanced_client = None

def get_enhanced_nba_client() -> EnhancedNBAApiClient:
    """Get global Enhanced NBA API Client instance"""
    global _enhanced_client
    if _enhanced_client is None:
        _enhanced_client = EnhancedNBAApiClient()
    return _enhanced_client