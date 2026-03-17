#!/bin/bash

# Balon d'Or - Quick Start Script
# This script builds the React frontend and starts the Django server

set -e  # Exit on error

echo "🏆 Balon d'Or - Quick Start"
echo "============================"
echo ""

# Check if we're in the correct directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "   Consider activating your virtual environment first:"
    echo "   source .venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build React frontend
echo "📦 Building React frontend..."
cd frontend

if ! command -v bun &> /dev/null; then
    echo "❌ Error: bun is not installed. Please install bun first."
    echo "   Visit: https://bun.sh"
    exit 1
fi

bun run build

if [ $? -ne 0 ]; then
    echo "❌ Error: React build failed."
    exit 1
fi

cd ..
echo "✅ React frontend built successfully!"
echo ""

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Error: Database migrations failed."
    exit 1
fi

echo "✅ Migrations completed!"
echo ""

# Start Django server
echo "🚀 Starting Django server..."
echo ""
echo "Application will be available at:"
echo "   Frontend: http://localhost:8000"
echo "   Admin:    http://localhost:8000/admin"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python manage.py collectstatic --noinput
python manage.py runserver
