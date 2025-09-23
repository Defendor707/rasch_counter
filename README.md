# Rasch Counter - Professional Test Analysis Platform

A comprehensive platform for IRT-based test analysis using the Rasch model. Available as Telegram bot, web application, and mobile app for maximum accessibility.

## 🌟 Features

### Core Analysis Engine
- **1PL IRT Model (Rasch Model)**: Implements one-parameter logistic model with ability (θ) and difficulty (β) parameters
- **Excel Processing**: Handles Excel files with student responses (0/1 format)
- **Statistical Analysis**: Provides comprehensive test analysis including:
  - Student ability estimates
  - Item difficulty analysis
  - Grade distribution
  - Pass/fail statistics

### Multiple Interfaces
- **🤖 Telegram Bot**: Mobile-friendly bot for quick analysis
- **🌐 Web Application**: Modern responsive web interface
- **📱 Mobile App**: Native React Native app for iOS/Android

### Export & Reporting
- **Multiple Export Formats**: 
  - Excel with detailed results and charts
  - PDF reports with formatted tables
  - Simplified Excel for quick reference
- **UZBMB Standards**: Grade assignments follow official UZBMB standards
- **Real-time Processing**: Live progress tracking and status updates

### Additional Features
- **Admin Panel**: Broadcast messages to all users (Telegram bot)
- **Database Tracking**: SQLite database for user and usage statistics
- **Sample Data**: Generate test data for demonstration

## Project Structure

```
rasch_counter/
├── src/                          # Core source code
│   ├── bot/                      # Telegram bot modules
│   │   ├── telegram_bot.py       # Main bot implementation
│   │   └── bot_database.py       # Database operations
│   ├── models/                   # Mathematical models
│   │   └── rasch_model.py        # Rasch/IRT model implementation
│   ├── data_processing/          # Data processing modules
│   │   └── data_processor.py     # Excel processing and analysis
│   ├── utils/                    # Utility functions
│   │   └── utils.py              # Helper functions
│   └── main.py                   # Telegram bot entry point
├── web_app/                      # Web application
│   ├── app.py                    # Flask web application
│   ├── templates/                # HTML templates
│   │   └── index.html            # Main web interface
│   ├── requirements.txt          # Web app dependencies
│   └── run_web.py               # Web app launcher
├── mobile_app/                   # Mobile application
│   ├── App.tsx                   # React Native main component
│   ├── package.json              # Mobile app dependencies
│   └── README.md                 # Mobile app documentation
├── config/                       # Configuration files
│   ├── settings.py               # Application settings
│   └── logging.py                # Logging configuration
├── docs/                         # Documentation
├── logs/                         # Log files (created at runtime)
├── .data/                        # Database and data files (created at runtime)
├── requirements.txt              # Core Python dependencies
├── bot.py                        # Telegram bot launcher
├── public_website.py             # Public information website
└── README.md                     # This file
```

## 🚀 Quick Start

### Option 1: Telegram Bot (Recommended for beginners)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up Telegram bot:**
```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
```

3. **Run the bot:**
```bash
python bot.py
```

4. **Start using:** Send `/start` to your bot on Telegram

### Option 2: Web Application

1. **Install web dependencies:**
```bash
pip install -r web_app/requirements.txt
```

2. **Run web app:**
```bash
python web_app/run_web.py
```

3. **Open browser:** Navigate to `http://localhost:5000`

### Option 3: Mobile App

1. **Install React Native CLI:**
```bash
npm install -g react-native-cli
```

2. **Install dependencies:**
```bash
cd mobile_app
npm install
```

3. **Run on device:**
```bash
# Android
npm run android

# iOS (macOS only)
npm run ios
```

## 📋 Prerequisites

- **Python 3.11+** (for bot and web app)
- **Node.js 16+** (for mobile app)
- **React Native CLI** (for mobile development)
- **Android Studio** (for Android development)
- **Xcode** (for iOS development, macOS only)

## Configuration

### Environment Variables

- `TELEGRAM_TOKEN`: Your Telegram bot token (required)
- `TELEGRAM_WEBHOOK_HOST`: Webhook host (optional, for production)
- `TELEGRAM_WEBHOOK_PORT`: Webhook port (default: 8443)
- `TELEGRAM_CERT_FILE`: SSL certificate file (for webhook)
- `TELEGRAM_KEY_FILE`: SSL key file (for webhook)
- `LOG_LEVEL`: Logging level (default: INFO)
- `IRT_MODEL`: IRT model type (1PL only, default: 1PL)

### Grade Standards

The bot uses UZBMB (Uzbekistan Agency for Assessment of Knowledge and Skills) grade standards:

- **A+**: 70+ points (1st grade - Excellent with honors)
- **A**: 65-69.9 points (1st grade - Excellent)
- **B+**: 60-64.9 points (2nd grade - Good with honors)
- **B**: 55-59.9 points (2nd grade - Good)
- **C+**: 50-54.9 points (3rd grade - Satisfactory with honors)
- **C**: 46-49.9 points (3rd grade - Satisfactory)
- **NC**: <46 points (4th grade - No certificate)

## Usage

### Bot Commands

- `/start` - Start the bot and get welcome message
- `/help` - Get help and usage instructions
- `/ball` - Calculate average scores from two Excel files
- `/matrix` - Get a sample Excel template
- `/cancel` - Cancel current operation
- `/adminos` - Admin panel (admin only)

### Excel File Format

Your Excel file should have:
- First column: Student ID/Name
- Remaining columns: Question responses (0 for incorrect, 1 for correct)
- Each row represents one student
- Each column represents one question

### Example Excel Structure

| Student ID | Q1 | Q2 | Q3 | ... | Q55 |
|------------|----|----|----|-----|-----|
| Student1   | 1  | 0  | 1  | ... | 1   |
| Student2   | 0  | 1  | 0  | ... | 1   |
| ...        | ...| ...| ...| ... | ... |

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

The project follows PEP 8 style guidelines. Use the following tools:

```bash
# Format code
black src/ tests/

# Check style
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Submit pull request

## API Reference

### Main Classes

- `RaschModel`: Implements the Rasch/IRT model
- `BotDatabase`: Handles database operations
- `DataProcessor`: Processes Excel files and generates reports

### Key Functions

- `rasch_model()`: Main model estimation function
- `process_exam_data()`: Process Excel file and return results
- `prepare_excel_for_download()`: Generate Excel report
- `prepare_pdf_for_download()`: Generate PDF report

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the project root directory
2. **Database Errors**: Check that the `.data` directory exists and is writable
3. **Memory Issues**: For large datasets, consider using the chunked processing option
4. **Telegram API Errors**: Verify your bot token and check API limits

### Logs

Check the logs directory for detailed error information:
```bash
tail -f logs/bot.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release
- 1PL IRT model (Rasch model) implementation
- Excel and PDF export functionality
- UZBMB grade standards
- Admin panel
- Database tracking