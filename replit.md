# Test Markazining Tahlil Platformasi (Test Center Analysis Platform)

## Overview

This is a Telegram bot-based educational testing analysis platform that implements the Rasch psychometric model for exam result processing. The system provides a Telegram bot interface for analyzing test results, calculating student abilities, item difficulties, and generating comprehensive reports with grade distributions. Web interface has been completely removed per user request.

## System Architecture

### Dual Interface Architecture
- **Primary Interface**: Streamlit web application (`app.py`) running on port 5000
- **Secondary Interface**: Telegram bot (`telegram_bot.py`) for mobile-friendly access
- **Orchestration**: Main controller (`main.py`) runs both interfaces in parallel threads

### Core Processing Engine
- **Rasch Model Implementation**: Advanced psychometric analysis using scipy optimization
- **Data Processing Pipeline**: Handles Excel/PDF input files with intelligent preprocessing
- **Statistical Analysis**: Comprehensive grade distribution and performance metrics

### Data Storage
- **SQLite Database**: Thread-safe user session management and bot data storage
- **JSON User Database**: Authentication and user management system
- **File-based Storage**: Temporary processing files in `.data` directory

## Key Components

### Authentication System (`users.py`)
- Secure password hashing with salt
- Session management with expiration
- Role-based access control (admin/user)
- Default admin account initialization

### Data Processing Pipeline (`data_processor.py`)
- **Intelligent Column Detection**: Automatically identifies student ID and question columns
- **Data Cleaning**: Standardizes input format to binary (0/1) responses
- **Multi-format Support**: Excel (.xlsx) and PDF processing capabilities
- **Report Generation**: PDF and Excel output with charts and statistics

### Rasch Model Engine (`rasch_model.py`)
- **Psychometric Analysis**: Estimates student abilities and item difficulties
- **Large Dataset Optimization**: Chunked processing for scalability
- **Grade Conversion**: Maps abilities to BBM standard grades (A+, A, B+, B, C+, C, NC)
- **Standard Score Calculation**: Converts raw abilities to interpretable scores

### Visualization & Analytics (`utils.py`)
- **Grade Distribution Charts**: Color-coded bar charts following BBM standards
- **Statistical Summaries**: Pass rates, averages, and distribution metrics
- **Mobile-Responsive Design**: Adaptive layouts for different screen sizes

### Bot Interface (`telegram_bot.py`)
- **File Upload Processing**: Handles Excel/PDF uploads via Telegram
- **Real-time Progress Updates**: Dynamic status messages during processing
- **Interactive Results**: Callback-based navigation and detailed statistics
- **Multi-threaded Processing**: Non-blocking analysis operations

## Data Flow

1. **Input Stage**: Users upload Excel/PDF files via web or Telegram interface
2. **Preprocessing**: Automatic detection and cleaning of student data and responses
3. **Rasch Analysis**: Statistical modeling to estimate abilities and difficulties
4. **Grade Assignment**: Conversion to BBM standard grades based on thresholds
5. **Report Generation**: Creation of comprehensive Excel/PDF reports with visualizations
6. **Output Delivery**: Results provided through charts, statistics, and downloadable files

## External Dependencies

### Core Processing Libraries
- **scipy**: Advanced optimization for Rasch model parameter estimation
- **pandas/numpy**: Data manipulation and numerical computations
- **matplotlib/plotly**: Visualization and charting capabilities

### Interface Libraries
- **streamlit**: Web application framework with real-time updates
- **telebot (pyTelegramBotAPI)**: Telegram bot API integration
- **reportlab**: PDF generation and document formatting

### Data Handling
- **openpyxl/xlsxwriter**: Excel file processing and creation
- **PyPDF2**: PDF file reading and manipulation
- **sqlite3**: Embedded database for user and session management

## Deployment Strategy

### Replit Autoscale Deployment
- **Primary Process**: Streamlit app on port 5000 (mapped to external port 80)
- **Background Process**: Telegram bot running concurrently
- **Resource Management**: Nix package manager for system dependencies
- **Persistent Storage**: SQLite database in `.data` directory for data persistence

### System Dependencies
- **Graphics Libraries**: cairo, freetype, ghostscript for PDF/chart generation
- **Media Processing**: ffmpeg for potential multimedia handling
- **GUI Libraries**: gtk3, tcl/tk for matplotlib backend support

### Environment Configuration
- **Python 3.11**: Primary runtime environment
- **Process Orchestration**: Thread-based parallel execution of web and bot interfaces
- **Port Configuration**: External access through port 80, internal on 5000

## Changelog

```
Changelog:
- June 26, 2025. Initial setup
- June 26, 2025. Complete website removal - app.py file completely deleted per user request
- June 26, 2025. System converted to Telegram bot only - main.py updated to run only bot
- June 26, 2025. Architecture simplified - single interface approach implemented
- June 26, 2025. Documentation updated to reflect bot-only platform
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
Project approach: Complete removal of unused features rather than disabling them to avoid bloat.
Design preference: Clean, modern interface without unnecessary complexity.
Performance priority: Speed and accuracy are essential for all features.
```