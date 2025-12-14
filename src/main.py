import subprocess
import sys
from pathlib import Path

def run_telegram_bot():
    """Telegram botni ishga tushirish"""
    print("Telegram bot ishga tushirilmoqda...")
    bot_path = Path(__file__).parent / "bot" / "telegram_bot.py"
    subprocess.run([sys.executable, str(bot_path)])

if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    run_telegram_bot()