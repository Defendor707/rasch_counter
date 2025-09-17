"""
Environment and configuration validation utilities
"""
import os
import sys
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def validate_environment() -> Tuple[bool, List[str]]:
    """
    Validate all required environment variables and configuration
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required environment variables
    required_vars = {
        'TELEGRAM_TOKEN': 'Telegram bot token is required',
    }
    
    # Check required variables
    for var, error_msg in required_vars.items():
        if not os.environ.get(var):
            errors.append(f"❌ {error_msg}")
        else:
            logger.debug(f"✅ {var} is set")
    
    # Validate Telegram token format
    token = os.environ.get('TELEGRAM_TOKEN')
    if token and not _validate_telegram_token(token):
        errors.append("❌ Invalid Telegram token format")
    
    # Validate Admin User ID
    admin_id = os.environ.get('ADMIN_USER_ID')
    if admin_id:
        try:
            admin_id_int = int(admin_id)
            if admin_id_int <= 0:
                errors.append("❌ ADMIN_USER_ID must be a positive integer")
        except ValueError:
            errors.append("❌ ADMIN_USER_ID must be a valid integer")
    else:
        logger.warning("⚠️ ADMIN_USER_ID not set, using default (0)")
    
    # Validate webhook settings if provided
    webhook_host = os.environ.get('TELEGRAM_WEBHOOK_HOST')
    cert_file = os.environ.get('TELEGRAM_CERT_FILE')
    key_file = os.environ.get('TELEGRAM_KEY_FILE')
    
    if webhook_host and (not cert_file or not key_file):
        errors.append("❌ Webhook host provided but certificate files missing")
    
    if cert_file and not os.path.exists(cert_file):
        errors.append(f"❌ Certificate file not found: {cert_file}")
    
    if key_file and not os.path.exists(key_file):
        errors.append(f"❌ Key file not found: {key_file}")
    
    # Validate log level
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level.upper() not in valid_levels:
        errors.append(f"❌ Invalid LOG_LEVEL: {log_level}. Must be one of {valid_levels}")
    
    # Validate IRT model
    irt_model = os.environ.get('IRT_MODEL', '1PL').upper()
    valid_models = ['1PL', '2PL']
    if irt_model not in valid_models:
        errors.append(f"❌ Invalid IRT_MODEL: {irt_model}. Must be one of {valid_models}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def _validate_telegram_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    if not token or not isinstance(token, str):
        return False
    
    # Telegram bot tokens are typically two parts separated by a colon
    # e.g., 123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    if not parts[0].isdigit():
        return False
    
    if len(parts[1]) < 10:  # Minimum length for the secret part
        return False
    
    return True

def validate_directories() -> Tuple[bool, List[str]]:
    """
    Validate that required directories exist and are writable
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required directories
    required_dirs = [
        ('.data', 'Data directory'),
        ('logs', 'Logs directory'),
        ('src', 'Source directory'),
        ('tests', 'Tests directory'),
    ]
    
    for dir_path, description in required_dirs:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"✅ Created {description}: {dir_path}")
            except Exception as e:
                errors.append(f"❌ Cannot create {description}: {e}")
        else:
            # Check if writable
            if not os.access(dir_path, os.W_OK):
                errors.append(f"❌ {description} is not writable: {dir_path}")
            else:
                logger.debug(f"✅ {description} is writable: {dir_path}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_dependencies() -> Tuple[bool, List[str]]:
    """
    Validate that all required Python packages are installed
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required packages
    required_packages = [
        'numpy',
        'pandas', 
        'scipy',
        'telebot',
        'reportlab',
        'openpyxl',
        'xlsxwriter',
        'psutil',
    ]
    
    for package in required_packages:
        try:
            __import__(package)
            logger.debug(f"✅ Package {package} is available")
        except ImportError:
            errors.append(f"❌ Required package not found: {package}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

def print_validation_summary(is_valid: bool, errors: List[str]) -> None:
    """Print validation summary"""
    if is_valid:
        print("✅ All validations passed!")
    else:
        print("❌ Validation failed:")
        for error in errors:
            print(f"  {error}")

def validate_all() -> bool:
    """
    Run all validations
    
    Returns:
        True if all validations pass, False otherwise
    """
    print("🔍 Running environment validation...")
    
    # Environment validation
    env_valid, env_errors = validate_environment()
    print_validation_summary(env_valid, env_errors)
    
    # Directory validation
    dir_valid, dir_errors = validate_directories()
    print_validation_summary(dir_valid, dir_errors)
    
    # Dependencies validation
    dep_valid, dep_errors = validate_dependencies()
    print_validation_summary(dep_valid, dep_errors)
    
    all_valid = env_valid and dir_valid and dep_valid
    all_errors = env_errors + dir_errors + dep_errors
    
    if not all_valid:
        print(f"\n💥 Total validation errors: {len(all_errors)}")
        print("Please fix the errors above before running the bot.")
    else:
        print("\n🎉 All validations passed! Bot is ready to run.")
    
    return all_valid

if __name__ == "__main__":
    validate_all()
