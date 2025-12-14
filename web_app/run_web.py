#!/usr/bin/env python3
"""
Web app ishga tushirish uchun script
"""

import os
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables
env_file = parent_dir / '.env'
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Import and run the web app
from web_app.app import app

if __name__ == '__main__':
    port = int(os.environ.get('WEB_PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Rasch Counter Web App")
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"📱 Mobile-friendly interface")
    print(f"🤖 Telegram bot ham ishlaydi")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
