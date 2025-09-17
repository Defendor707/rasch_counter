"""
Logging configuration for Rasch Counter Bot
"""
import logging
import logging.handlers
from pathlib import Path
from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logging():
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format=LOG_FORMAT,
        handlers=[
            # Console handler
            logging.StreamHandler(),
            # File handler with rotation
            logging.handlers.RotatingFileHandler(
                LOGS_DIR / "bot.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Configure specific loggers
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    # Bot-specific logger
    bot_logger = logging.getLogger("rasch_bot")
    bot_logger.setLevel(logging.INFO)
    
    return bot_logger
