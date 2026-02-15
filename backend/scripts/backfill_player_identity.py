import sys

sys.path.insert(0, "/Users/marvens/Desktop/Karchain/backend")

from app.database import SessionLocal
from app.player_identity_sync import backfill_player_identity_and_media


def main():
    db = SessionLocal()
    try:
        result = backfill_player_identity_and_media(db)
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    main()

