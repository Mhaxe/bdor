#!/bin/bash

# Build script for Vercel deployment
# This script builds the React frontend and collects static files for Django.

set -e  # Exit on error

# Ensure we are in project root
if [ ! -f "manage.py" ]; then
  echo "❌ Error: manage.py not found. Please run this script from the project root."
  exit 1
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

cd ..
echo "✅ React frontend built successfully!"

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Static files collected!"
