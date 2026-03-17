"
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

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    echo "🔄 Activating virtual environment..."
    source .venv/bin/activate
fi


# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ Error: Database migrations failed."
    exit 1
fi

echo "✅ Migrations completed!"
echo ""

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput