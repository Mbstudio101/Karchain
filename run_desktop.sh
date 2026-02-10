#!/bin/bash

# Kill any existing processes on ports 8000 and 1420
echo "Cleaning up existing processes..."
kill -9 $(lsof -ti:8000) 2>/dev/null
kill -9 $(lsof -ti:1420) 2>/dev/null

echo "Starting Backend..."
cd backend && python3 -m uvicorn app.main:app --reload &

sleep 3

echo "Starting Frontend..."
cd /Users/marvens/Desktop/Karchain/frontend && npm run tauri dev