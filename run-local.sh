#!/bin/bash

echo "🚀 Starting Vocalis SaaS Development Server..."

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
cd backend
pip install -r requirements.txt

# Check for .env file
if [ ! -f "../.env" ]; then
    echo "⚠️  Creating .env file from template..."
    cp ../.env.example ../.env
    echo "Please edit .env file with your configuration"
fi

# Start the server
echo "🚀 Starting FastAPI server..."
python -m app.main

