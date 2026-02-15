from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import games, teams, recommendations, players, auth, self_improvement
from .database import engine, Base, SessionLocal
from .brain import start_scheduler, shutdown_scheduler
from .models import Game
from .background_sync import start_background_sync, stop_background_sync
from .websocket_manager import manager, notify_data_update
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Initialize database with required data
    db = SessionLocal()
    try:
        from .db_init import init_db
        init_db(db)
        
        # Check if we need to sync data
        from .data_sync_service import data_sync_service
        sync_performed = data_sync_service.sync_if_needed(db)
        
        if sync_performed:
            print("🧠 Startup: Data sync completed successfully!")
        else:
            print("🧠 Startup: Database is up to date.")
            
    except Exception as e:
        print(f"🧠 Startup Error: {e}")
    finally:
        db.close()

    start_scheduler()
    
    # Start background sync service for 24/7 automatic updates
    start_background_sync()
    print("🔄 Background sync service started for 24/7 automatic updates")
    
    yield
    # Shutdown
    shutdown_scheduler()
    stop_background_sync()

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

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data updates."""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to Karchain real-time updates"
            }), 
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    data_type = message.get("data_type")
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscription_confirmed",
                            "data_type": data_type,
                            "message": f"Subscribed to {data_type} updates"
                        }),
                        websocket
                    )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON format"}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/ws/status")
def websocket_status():
    """Get WebSocket connection status."""
    return {
        "active_connections": manager.get_connection_count(),
        "status": "running"
    }
