#!/usr/bin/env python3
"""
Simple run script for Rasch Counter Bot
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Set environment variables if not set
if not os.environ.get("TELEGRAM_TOKEN"):
    print("Error: TELEGRAM_TOKEN environment variable is required")
    print("Please set it with: export TELEGRAM_TOKEN=your_token_here")
    sys.exit(1)

# Import and run the main function
from main import run_telegram_bot

if __name__ == "__main__":
    run_telegram_bot()
