# Rasch Counter Bot

A Telegram bot for IRT-based test analysis using the Rasch model. This bot processes Excel files containing student test responses and provides detailed analysis including ability estimates, item difficulty analysis, and grade assignments according to UZBMB standards.

## Features

- **1PL IRT Model (Rasch Model)**: Implements one-parameter logistic model with ability (θ) and difficulty (β) parameters
- **Excel Processing**: Handles Excel files with student responses (0/1 format)
- **Statistical Analysis**: Provides comprehensive test analysis including:
  - Student ability estimates
  - Item difficulty analysis
  - Grade distribution
  - Pass/fail statistics
- **Multiple Export Formats**: 
  - Excel with detailed results and charts
  - PDF reports with formatted tables
  - Simplified Excel for quick reference
- **UZBMB Standards**: Grade assignments follow official UZBMB standards
- **Admin Panel**: Broadcast messages to all users
- **Database Tracking**: SQLite database for user and usage statistics

## Project Structure

```
rasch_counter/
├── src/                          # Source code
│   ├── bot/                      # Bot-related modules
│   │   ├── telegram_bot.py       # Main bot implementation
│   │   └── bot_database.py       # Database operations
│   ├── models/                   # Mathematical models
│   │   └── rasch_model.py        # Rasch/IRT model implementation
│   ├── data_processing/          # Data processing modules
│   │   └── data_processor.py     # Excel processing and analysis
│   ├── utils/                    # Utility functions
│   │   └── utils.py              # Helper functions
│   └── main.py                   # Application entry point
├── config/                       # Configuration files
│   ├── settings.py               # Application settings
│   └── logging.py                # Logging configuration
├── tests/                        # Test files
│   ├── test_rasch_model.py       # Model tests
│   └── test_real_data.py         # Real data tests
├── deployment/                   # Deployment files
│   ├── docker-compose.yml        # Docker Compose configuration
│   ├── Dockerfile                # Docker configuration
│   └── rasch-bot.service         # Systemd service file
├── docs/                         # Documentation
├── logs/                         # Log files (created at runtime)
├── .data/                        # Database and data files (created at runtime)
├── assets/                       # Static assets
├── requirements.txt              # Python dependencies
├── setup.py                      # Package setup
├── pyproject.toml                # Project configuration
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Local Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rasch_counter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export TELEGRAM_TOKEN="your_telegram_bot_token"
```

4. Run the bot:
```bash
python src/main.py
```

### Docker Installation

1. Build the Docker image:
```bash
docker build -t rasch-counter-bot .
```

2. Run with Docker Compose:
```bash
cd deployment
docker-compose up -d
```

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