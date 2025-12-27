#!/bin/bash
set -e

#echo "🚀 Starting Stock AI Platform API..."

# Ensure we're in the api directory
cd "$(dirname "$0")"

#echo "📦 Installing dependencies..."
#pip install -r requirements.txt

echo "✅ Launching API server..."
uvicorn app.main:app --host 0.0.0.0 --port 5000
