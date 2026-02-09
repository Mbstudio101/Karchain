
import asyncio
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import engine, Base
from app.models import Game

async def verify_tables():
    print("Verifying tables via SQLAlchemy...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")

    if 'games' in tables:
        print("games table exists.")
        columns = [c['name'] for c in inspector.get_columns('games')]
        print(f"Columns in games table: {columns}")
    else:
        print("games table DOES NOT exist.")

if __name__ == "__main__":
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(verify_tables())
