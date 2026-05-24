#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starter Politikerapp..."
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo ""
echo "Trykk Ctrl+C for å stoppe."
echo ""

# Start backend
cd "$SCRIPT_DIR/backend"
source .venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Start frontend
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

# Rydd opp ved Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
