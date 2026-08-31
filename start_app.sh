#!/bin/bash
set -e

echo "🧠 ZeptoBrain Startup..."
echo ""

# Check if data files exist, if not generate them
if [ ! -f "data/inventory_history.csv" ] || [ ! -f "data/stores.json" ]; then
    echo "📊 Generating data files..."
    python3 data/generate_data.py
else
    echo "✅ Data files found"
fi

# Train ML model if not exists
if [ ! -f "ml/demand_model.pkl" ]; then
    echo "🤖 Training ML model..."
    python3 ml/demand_forecast.py
else
    echo "✅ ML model found"
fi

echo ""
echo "🚀 Starting FastAPI server..."
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
