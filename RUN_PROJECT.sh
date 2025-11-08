#!/bin/bash

echo "🚀 Starting CareerLens AI..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Create .env file with your API keys (see QUICK_START.md)"
    echo ""
fi

# Start backend
echo "📦 Starting Backend Server..."
cd backend
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3.11 -m venv venv
fi

source venv/bin/activate

if [ ! -f "venv/bin/activate" ]; then
    echo "   Installing dependencies..."
    pip install -r requirements.txt
fi

echo "   Backend starting on http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""

# Start backend in background
make dev &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend
echo "🎨 Starting Frontend Server..."
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

echo "   Frontend starting on http://localhost:5173"
echo ""

# Start frontend
npm run dev &
FRONTEND_PID=$!

echo "✅ Both servers are starting!"
echo ""
echo "📝 To stop servers, press Ctrl+C or run:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
