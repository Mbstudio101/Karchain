from __future__ import annotations

import logging
import re
import unicodedata
from typing import Dict, Optional

from sqlalchemy.orm import Session

from app import models

logger = logging.getLogger(__name__)

NBA_HEADSHOT_URL = "https://cdn.nba.com/headshots/nba/latest/260x190/{player_id}.png"

# NBA API team IDs -> canonical team names
NBA_TEAM_ID_TO_NAME: Dict[int, str] = {
    1610612737: "Atlanta Hawks",
    1610612738: "Boston Celtics",
    1610612751: "Brooklyn Nets",
    1610612766: "Charlotte Hornets",
    1610612741: "Chicago Bulls",
    1610612739: "Cleveland Cavaliers",
    1610612742: "Dallas Mavericks",
    1610612743: "Denver Nuggets",
    1610612765: "Detroit Pistons",
    1610612744: "Golden State Warriors",
    1610612745: "Houston Rockets",
    1610612754: "Indiana Pacers",
    1610612746: "Los Angeles Clippers",
    1610612747: "Los Angeles Lakers",
    1610612763: "Memphis Grizzlies",
    1610612748: "Miami Heat",
    1610612749: "Milwaukee Bucks",
    1610612750: "Minnesota Timberwolves",
    1610612740: "New Orleans Pelicans",
    1610612752: "New York Knicks",
    1610612760: "Oklahoma City Thunder",
    1610612753: "Orlando Magic",
    1610612755: "Philadelphia 76ers",
    1610612756: "Phoenix Suns",
    1610612757: "Portland Trail Blazers",
    1610612758: "Sacramento Kings",
    1610612759: "San Antonio Spurs",
    1610612761: "Toronto Raptors",
    1610612762: "Utah Jazz",
    1610612764: "Washington Wizards",
}


def _normalize_name(name: str) -> str:
    if not name:
        return ""
    # Strip accents/diacritics to match variants like Schroder/Schroeder, Nurkic/Nurkic.
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[.\-']", " ", s)
    s = re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _build_static_players_lookup() -> Dict[str, int]:
    """
    Build name -> NBA player id map from nba_api static registry.
    Prefer active players on duplicate names.
    """
    from nba_api.stats.static import players as nba_players

    by_name: Dict[str, int] = {}
    for row in nba_players.get_players():
        full_name = (row.get("full_name") or "").strip()
        nba_id = row.get("id")
        if not full_name or not nba_id:
            continue

        key = _normalize_name(full_name)
        # Prefer active player row when duplicates exist.
        is_active = bool(row.get("is_active"))
        if key not in by_name or is_active:
            by_name[key] = int(nba_id)
    return by_name


def _build_current_team_lookup_by_name() -> Dict[str, int]:
    """
    Build normalized player name -> NBA TEAM_ID from current season stats table.
    """
    from nba_api.stats.endpoints import leaguedashplayerstats

    out: Dict[str, int] = {}
    try:
        df = leaguedashplayerstats.LeagueDashPlayerStats(
            season="2025-26",
            season_type_all_star="Regular Season",
            per_mode_detailed="PerGame",
        ).get_data_frames()[0]

        for _, row in df.iterrows():
            name = str(row.get("PLAYER_NAME") or "").strip()
            team_id = row.get("TEAM_ID")
            if not name or team_id is None:
                continue
            try:
                out[_normalize_name(name)] = int(team_id)
            except Exception:
                continue
    except Exception as e:
        logger.warning("Could not build current-team lookup from NBA API: %s", e)

    return out


def backfill_player_identity_and_media(db: Session) -> Dict[str, int]:
    """
    1) Fill player.headshot_url using real NBA player IDs (name-matched).
    2) Normalize players.team_id from external NBA IDs to internal teams.id.
    """
    teams = db.query(models.Team).all()
    team_id_by_name = {t.name: t.id for t in teams}

    # Also support LA Clippers alias in source data.
    if "Los Angeles Clippers" in team_id_by_name and "LA Clippers" not in team_id_by_name:
        team_id_by_name["LA Clippers"] = team_id_by_name["Los Angeles Clippers"]

    static_lookup = _build_static_players_lookup()
    current_team_lookup = _build_current_team_lookup_by_name()
    players = db.query(models.Player).all()

    headshots_updated = 0
    teams_normalized = 0
    names_unmatched = 0

    for p in players:
        # Normalize team linkage if current team_id is external NBA team ID.
        if p.team_id in NBA_TEAM_ID_TO_NAME:
            team_name = NBA_TEAM_ID_TO_NAME[p.team_id]
            internal_id = team_id_by_name.get(team_name)
            if internal_id and p.team_id != internal_id:
                p.team_id = internal_id
                teams_normalized += 1
        elif p.team_id is None:
            # Fill missing team_id using current NBA team data by player name.
            nba_team_id = current_team_lookup.get(_normalize_name(p.name))
            if nba_team_id in NBA_TEAM_ID_TO_NAME:
                mapped_team_name = NBA_TEAM_ID_TO_NAME[nba_team_id]
                internal_id = team_id_by_name.get(mapped_team_name)
                if internal_id:
                    p.team_id = internal_id
                    teams_normalized += 1

        # Fill headshot with real NBA CDN URL via name->id mapping.
        if not p.headshot_url:
            nba_id: Optional[int] = None
            if p.id >= 100000:
                nba_id = p.id
            else:
                nba_id = static_lookup.get(_normalize_name(p.name))

            if nba_id:
                p.headshot_url = NBA_HEADSHOT_URL.format(player_id=nba_id)
                headshots_updated += 1
            else:
                names_unmatched += 1

    db.commit()
    return {
        "headshots_updated": headshots_updated,
        "teams_normalized": teams_normalized,
        "names_unmatched": names_unmatched,
        "total_players": len(players),
    }
