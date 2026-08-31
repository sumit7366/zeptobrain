#!/bin/bash
# ZeptoBrain — One-command startup script

echo "🧠 ZeptoBrain Setup Starting..."
echo "================================"

# Install dependencies
echo "📦 Installing dependencies..."
pip install fastapi uvicorn pandas numpy scikit-learn xgboost sqlalchemy python-dotenv pytest httpx faker --break-system-packages -q

# Generate data
echo "📊 Generating inventory data..."
python3 data/generate_data.py

# Train model
echo "🤖 Training XGBoost model..."
python3 ml/demand_forecast.py

# Run tests
echo "🧪 Running tests..."
python3 tests/test_all.py

# Start backend
echo "🚀 Starting FastAPI backend on port 8000..."
echo "   API Docs: http://localhost:8000/docs"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
