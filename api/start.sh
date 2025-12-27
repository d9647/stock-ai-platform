#!/bin/bash
# Startup script for Stock AI Platform API on Replit

echo "🚀 Starting Stock AI Platform API..."

# Navigate to api directory
cd "$(dirname "$0")"

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "🗄️  Running database migrations..."
python -m alembic upgrade head

# Start the API server
echo "✅ Starting API server on port 8000..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
