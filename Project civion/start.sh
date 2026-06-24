#!/bin/bash

# Civion AI Startup Script

# 1. Set your Groq API Key (Replace with your actual key if needed)
export GROQ_API_KEY="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"

echo "Starting Civion AI..."
echo "=========================================="

# 2. Start the FastAPI Backend in the background
echo "[1/2] Starting FastAPI Backend on http://127.0.0.1:8000..."
uvicorn main:app --reload &
BACKEND_PID=$!

# 3. Start the Vite Frontend in the background
echo "[2/2] Starting React Frontend on http://localhost:5173..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo "=========================================="
echo "Civion AI is running! Press Ctrl+C to stop both servers."

# Trap Ctrl+C (SIGINT) to kill both background processes
trap "echo '\nStopping servers...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

# Wait indefinitely so the script doesn't exit immediately
wait
