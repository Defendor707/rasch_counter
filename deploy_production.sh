#!/bin/bash
# Production server uchun deployment script

echo "🚀 Rasch Counter Bot - Production Deployment"
echo "============================================="

# Environment setup
echo "📋 Setting up production environment..."
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export IRT_MODEL=1PL

# Load production environment variables
if [ -f "production.env" ]; then
    echo "📄 Loading production.env..."
    export $(cat production.env | grep -v '^#' | xargs)
fi

# Check Python dependencies
echo "🔍 Checking Python dependencies..."
python3 -c "import pandas, numpy, scipy, telebot" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip3 install -r requirements.txt
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p .data
mkdir -p assets

# Set permissions
echo "🔐 Setting permissions..."
chmod 755 logs
chmod 755 .data
chmod 755 assets

# Test the fixes
echo "🧪 Testing production fixes..."
python3 test_production_fixes.py

if [ $? -eq 0 ]; then
    echo "✅ Production fixes test passed!"
else
    echo "❌ Production fixes test failed!"
    exit 1
fi

# Start the bot
echo "🤖 Starting Rasch Counter Bot..."
echo "Environment: $ENVIRONMENT"
echo "Log Level: $LOG_LEVEL"
echo "IRT Model: $IRT_MODEL"

# Run the bot
python3 src/main.py
