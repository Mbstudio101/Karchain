
from sqlalchemy import create_engine, inspect
from app.database import DATABASE_URL

def check_schema():
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    columns = inspector.get_columns('player_props')
    column_names = [col['name'] for col in columns]
    print(f"Columns in player_props: {column_names}")
    
    if 'sportsbook' in column_names:
        print("Sportsbook column exists.")
    else:
        print("Sportsbook column MISSING.")

if __name__ == "__main__":
    check_schema()
