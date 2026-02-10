from app.database import engine
from sqlalchemy import text

def add_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE betting_odds ADD COLUMN additional_props JSON;"))
            print("Column 'additional_props' added successfully.")
        except Exception as e:
            print(f"Error adding column (might already exist): {e}")

if __name__ == "__main__":
    add_column()
