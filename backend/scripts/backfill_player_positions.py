"""Backfill missing player positions from NBA Stats commonplayerinfo endpoint."""
import time
from typing import Optional

import requests

from app.database import SessionLocal
from app import models

NBA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://stats.nba.com/",
    "Origin": "https://stats.nba.com",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
}

URL = "https://stats.nba.com/stats/commonplayerinfo"


def fetch_position(session: requests.Session, player_id: int) -> Optional[str]:
    params = {"LeagueID": "00", "PlayerID": str(player_id)}
    for _ in range(3):
        try:
            resp = session.get(URL, params=params, timeout=15)
            if resp.status_code != 200:
                time.sleep(0.4)
                continue
            data = resp.json()
            sets = data.get("resultSets") or []
            if not sets:
                return None
            headers = sets[0].get("headers") or []
            rows = sets[0].get("rowSet") or []
            if not rows:
                return None
            row = rows[0]
            item = dict(zip(headers, row))
            position = (item.get("POSITION") or "").strip()
            return position or None
        except Exception:
            time.sleep(0.4)
    return None


def main() -> None:
    db = SessionLocal()
    session = requests.Session()
    session.headers.update(NBA_HEADERS)

    try:
        missing_players = (
            db.query(models.Player)
            .filter((models.Player.position.is_(None)) | (models.Player.position == "") | (models.Player.position == "N/A"))
            .all()
        )

        print(f"Players missing position: {len(missing_players)}")

        updated = 0
        checked = 0
        for player in missing_players:
            checked += 1
            pos = fetch_position(session, int(player.id))
            if pos:
                player.position = pos
                updated += 1

            if checked % 50 == 0:
                db.commit()
                print(f"Checked {checked}/{len(missing_players)} | Updated {updated}")

            # Keep request cadence modest.
            time.sleep(0.15)

        db.commit()
        print(f"Done. Updated positions: {updated}")

    finally:
        db.close()
        session.close()


if __name__ == "__main__":
    main()
