import subprocess
import sys

def run_telegram_bot():
    """Telegram botni ishga tushirish"""
    print("Telegram bot ishga tushirilmoqda...")
    subprocess.run([sys.executable, "telegram_bot.py"])

if __name__ == "__main__":
    print("Bot ishga tushirilmoqda...")
    run_telegram_bot()