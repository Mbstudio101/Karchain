from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import games, teams, recommendations, players, auth, self_improvement
from .database import engine, Base, SessionLocal
from .brain import start_scheduler, shutdown_scheduler
from .models import Game
from datetime import datetime

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Check if we have games for today
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        game_count = db.query(Game).filter(Game.game_date >= today).count()
        if game_count == 0:
            print("🧠 Startup: No games found for today. Triggering initial sync...")
            from scrapers.espn_sync import sync_upcoming_games
            from scrapers.nba_official_sync import sync_official_scoreboard
            sync_official_scoreboard()
            sync_upcoming_games(1)
    except Exception as e:
        print(f"🧠 Startup Sync Error: {e}")
    finally:
        db.close()

    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()

app = FastAPI(title="Karchain API", version="0.1.0", lifespan=lifespan)

# CORS setup
origins = [
    "http://localhost",
    "http://localhost:1420",  # Tauri dev
    "http://localhost:3000",
    "http://localhost:5173", # Vite default
    "*"  # Allow all for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(games.router)
app.include_router(teams.router)
app.include_router(recommendations.router)
app.include_router(players.router)
app.include_router(auth.router)
app.include_router(self_improvement.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Karchain API", "brain": "active"}

@app.get("/health")
def health_check():
    return {"status": "ok", "brain": "running"}
