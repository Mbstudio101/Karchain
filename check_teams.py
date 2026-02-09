from app.database import SessionLocal
from app.models import Team

def check_teams():
    db = SessionLocal()
    teams = db.query(Team).all()
    for t in teams:
        print(f"ID: {t.id}, Name: {t.name}")
    db.close()

if __name__ == "__main__":
    check_teams()
