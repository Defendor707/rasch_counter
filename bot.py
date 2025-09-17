#!/usr/bin/env python3
"""
Rasch Counter Bot - Asosiy Bot Fayli
Test natijalarini Rasch model orqali tahlil qilish boti
"""

import os
import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from bot.telegram_bot import main

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

if __name__ == "__main__":
    # Load .env file
    load_env_file()
    
    # Start the bot
    main()
