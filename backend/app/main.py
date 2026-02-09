from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import games, teams, recommendations, players, auth
from .database import engine, Base
from .brain import start_scheduler, shutdown_scheduler

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Karchain API", "brain": "active"}

@app.get("/health")
def health_check():
    return {"status": "ok", "brain": "running"}
