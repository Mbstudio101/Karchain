
from sqlalchemy import create_engine, text
from app.database import DATABASE_URL

def add_sportsbook_column():
    """Add sportsbook column to player_props table"""
    engine = create_engine(DATABASE_URL)
    
    # Use text() to execute raw SQL
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE player_props ADD COLUMN sportsbook VARCHAR(50);"))
    print("Sportsbook column added successfully!")

if __name__ == "__main__":
    add_sportsbook_column()
