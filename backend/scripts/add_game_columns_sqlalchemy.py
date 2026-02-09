
import sys
import os
from sqlalchemy import text

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine

def add_columns():
    print("Connecting to database via SQLAlchemy...")
    with engine.connect() as conn:
        columns_to_add = [
            ("status", "VARCHAR DEFAULT 'Scheduled'"),
            ("home_score", "INTEGER DEFAULT 0"),
            ("away_score", "INTEGER DEFAULT 0"),
            ("quarter", "VARCHAR"),
            ("clock", "VARCHAR")
        ]
        
        for col_name, col_type in columns_to_add:
            try:
                print(f"Attempting to add column '{col_name}'...")
                conn.execute(text(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}"))
                print(f"Successfully added '{col_name}'")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    print(f"Column '{col_name}' already exists. Skipping.")
                else:
                    print(f"Error adding '{col_name}': {e}")
        
        conn.commit()
    print("Database schema update complete.")

if __name__ == "__main__":
    add_columns()
