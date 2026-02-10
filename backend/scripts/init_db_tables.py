from sqlalchemy import create_engine
from app.models import Base
from app.database import DATABASE_URL

def init_db():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    init_db()
