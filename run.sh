#!/bin/bash

# CV Reader Agent Pipeline - Startup Script
# Prerequisites: Docker, Docker Compose installed

echo "🚀 Starting CV Reader Agent Pipeline..."
echo ""

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Edit it if needed."
    echo ""
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "🐳 Docker is installed. Starting services..."
echo ""

# Start services
docker-compose up --build

echo ""
echo "✅ Services started successfully!"
echo ""
echo "📌 Access the application:"
echo "   - Streamlit UI: http://localhost:8501"
echo "   - FastAPI Docs: http://localhost:8000/docs"
echo "   - API Health: http://localhost:8000/health"
echo ""
echo "🛑 To stop the services, press Ctrl+C or run: docker-compose down"
