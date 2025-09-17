"""
Configuration settings for Rasch Counter Bot
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / ".data"
LOGS_DIR = PROJECT_ROOT / "logs"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database settings
DATABASE_PATH = DATA_DIR / "bot_data.db"

# Telegram Bot settings
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_WEBHOOK_HOST = os.environ.get("TELEGRAM_WEBHOOK_HOST")
TELEGRAM_WEBHOOK_PORT = int(os.environ.get("TELEGRAM_WEBHOOK_PORT", "8443"))
TELEGRAM_CERT_FILE = os.environ.get("TELEGRAM_CERT_FILE")
TELEGRAM_KEY_FILE = os.environ.get("TELEGRAM_KEY_FILE")

# Admin settings
ADMIN_USER_ID = 7537966029

# Model settings
IRT_MODEL = os.environ.get('IRT_MODEL', '1PL').upper()
REG_LAMBDA = 0.05  # L2 regularization parameter

# Performance settings
MAX_WORKERS = min(int(os.cpu_count() * 0.8), 4) if os.cpu_count() else 4
MAX_STUDENTS_CHUNK = 2000

# Logging settings
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Grade thresholds (UZBMB standards)
GRADE_THRESHOLDS = {
    'A+': 70,
    'A': 65,
    'B+': 60,
    'B': 55,
    'C+': 50,
    'C': 46,
    'NC': 0
}

# Grade descriptions
GRADE_DESCRIPTIONS = {
    'A+': '1-Daraja (Oliy Imtiyozli)',
    'A': '1-Daraja (Oliy)',
    'B+': '2-Daraja (Yuqori Imtiyozli)',
    'B': '2-Daraja (Yuqori)',
    'C+': '3-Daraja (O\'rta Imtiyozli)',
    'C': '3-Daraja (O\'rta)',
    'NC': '4-Daraja (Sertifikatsiz)'
}

# Grade colors for visualization
GRADE_COLORS = {
    'A+': '#006400',  # Dark green
    'A': '#28B463',   # Green
    'B+': '#1A237E',  # Dark blue
    'B': '#3498DB',   # Blue
    'C+': '#8D6E63',  # Brown
    'C': '#F4D03F',   # Yellow
    'NC': '#E74C3C'   # Red
}
