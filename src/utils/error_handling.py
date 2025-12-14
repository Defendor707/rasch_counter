"""
Error handling utilities for Rasch Counter Bot
"""
import os
import logging
import traceback
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def handle_errors(default_return=None, log_error=True):
    """
    Decorator for handling errors in bot functions
    
    Args:
        default_return: Value to return if error occurs
        log_error: Whether to log the error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_error:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                    logger.error(traceback.format_exc())
                return default_return
        return wrapper
    return decorator

def validate_excel_file(file_path: str) -> tuple[bool, str]:
    """
    Validate Excel file format and content
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        import pandas as pd
        
        # Check if file exists
        if not file_path or not os.path.exists(file_path):
            return False, "Fayl topilmadi"
        
        # Try to read the file
        df = pd.read_excel(file_path)
        
        # Check if file is empty
        if df.empty:
            return False, "Fayl bo'sh"
        
        # Check minimum requirements
        if len(df.columns) < 2:
            return False, "Faylda kamida 2 ta ustun bo'lishi kerak (talaba ismi + savollar)"
        
        if len(df) < 1:
            return False, "Faylda kamida 1 ta talaba bo'lishi kerak"
        
        # Check for valid data types
        for col in df.columns[1:]:  # Skip first column (student names)
            if not pd.api.types.is_numeric_dtype(df[col]):
                # Try to convert to numeric
                try:
                    pd.to_numeric(df[col], errors='raise')
                except:
                    return False, f"Ustun '{col}' raqamli ma'lumotlar emas"
        
        return True, ""
        
    except Exception as e:
        return False, f"Fayl o'qishda xatolik: {str(e)}"

def validate_telegram_token(token: str) -> bool:
    """
    Validate Telegram bot token format
    
    Args:
        token: Telegram bot token
        
    Returns:
        True if valid, False otherwise
    """
    if not token:
        return False
    
    # Basic format validation
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    if not parts[0].isdigit():
        return False
    
    if len(parts[1]) < 30:
        return False
    
    return True

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to int
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        Int value or default
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
