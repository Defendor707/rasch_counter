@echo off
chcp 65001 >nul
echo ========================================
echo Rasch Counter Telegram Bot
echo ========================================
echo.

cd /d "%~dp0"

echo 1. Token tekshirilmoqda...
if not exist .env (
    echo XATOLIK: .env fayl topilmadi!
    echo Token .env faylga yozilganligini tekshiring.
    pause
    exit /b 1
)

echo 2. Kutubxonalar tekshirilmoqda...
python -c "import telebot" 2>nul
if errorlevel 1 (
    echo pyTelegramBotAPI o'rnatilmagan. O'rnatilmoqda...
    python -m pip install pyTelegramBotAPI
)

python -c "import pandas" 2>nul
if errorlevel 1 (
    echo Pandas o'rnatilmagan. O'rnatilmoqda...
    python -m pip install pandas numpy openpyxl matplotlib flask reportlab
)

echo.
echo 3. Bot ishga tushirilmoqda...
echo.
python bot.py

pause
