
import sys
import os
import sqlite3

# Define absolute path to database
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'karchain.db'))

def add_columns():
    print(f"Connecting to database at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='games'")
    if not cursor.fetchone():
        print("Error: Table 'games' not found in database.")
        conn.close()
        return

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
            cursor.execute(f"ALTER TABLE games ADD COLUMN {col_name} {col_type}")
            print(f"Successfully added '{col_name}'")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"Column '{col_name}' already exists. Skipping.")
            else:
                print(f"Error adding '{col_name}': {e}")
                
    conn.commit()
    conn.close()
    print("Database schema update complete.")

if __name__ == "__main__":
    add_columns()
