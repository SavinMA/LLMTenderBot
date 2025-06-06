#!/bin/bash

# LLMTenderBot Deployment Script
# Usage: ./deploy.sh [dev|prod]

set -e

ENVIRONMENT=${1:-dev}
COMPOSE_FILE="docker-compose.yml"

if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

echo "🚀 Deploying LLMTenderBot in $ENVIRONMENT mode..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy example.env to .env and configure it."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs data

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f $COMPOSE_FILE up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo "📊 Checking service status..."
docker-compose -f $COMPOSE_FILE ps

# Test Ollama connection
echo "🧪 Testing Ollama connection..."
timeout 30 bash -c 'until curl -f http://localhost:11434/api/tags 2>/dev/null; do sleep 2; done' && echo "✅ Ollama is ready" || echo "⚠️ Ollama might not be ready yet"

# Show logs
echo "📝 Recent logs:"
docker-compose -f $COMPOSE_FILE logs --tail=20

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop: docker-compose -f $COMPOSE_FILE down"
echo "  Restart: docker-compose -f $COMPOSE_FILE restart"
echo "  Pull Ollama model: docker exec -it ollama ollama pull llama3.2:3b"
echo ""

if [ "$ENVIRONMENT" = "prod" ]; then
    echo "🔒 Production mode: Services are bound to localhost only"
fi 