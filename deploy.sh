#!/bin/bash

# Rasch Counter Bot Deployment Script
# Bu script oddiy monitoring bilan botni ishga tushiradi

set -e

echo "🚀 Rasch Counter Bot Deployment Script"
echo "======================================"

# Check if TELEGRAM_TOKEN is set
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "❌ Error: TELEGRAM_TOKEN environment variable is required"
    echo "Please set it with: export TELEGRAM_TOKEN=your_token_here"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker first"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose first"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs

# Set permissions
chmod 755 data logs

echo "🔧 Building Docker image..."
docker build -t rasch-counter-bot .

echo "🚀 Starting services..."

# Choose deployment type
if [ "$1" = "monitoring" ]; then
    echo "📊 Starting with full monitoring (Grafana + Prometheus)..."
    docker-compose -f deployment/simple-monitoring.yml up -d
    echo ""
    echo "✅ Services started!"
    echo "📊 Grafana: http://localhost:3000 (admin/admin123)"
    echo "📈 Prometheus: http://localhost:9090"
    echo "🤖 Bot Health: http://localhost:8443/health"
    echo "📊 Bot Metrics: http://localhost:8443/metrics"
else
    echo "🤖 Starting simple deployment..."
    docker-compose up -d
    echo ""
    echo "✅ Bot started!"
    echo "🤖 Bot Health: http://localhost:8443/health"
    echo "📊 Bot Stats: http://localhost:8443/stats"
fi

echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Update: docker-compose pull && docker-compose up -d"
echo ""
echo "🎉 Deployment completed!"
