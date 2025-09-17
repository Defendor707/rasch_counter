"""
Performance optimization utilities for Rasch Counter Bot
"""
import time
import psutil
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor function performance
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            result = func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            execution_time = end_time - start_time
            memory_used = end_memory - start_memory
            
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s, "
                       f"memory used: {memory_used:.2f}MB")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {str(e)}")
            raise
    
    return wrapper

def get_cpu_load() -> float:
    """
    Get current CPU load
    
    Returns:
        CPU load as float
    """
    try:
        with open('/proc/loadavg', 'r') as f:
            load = float(f.read().split()[0])
        return load
    except:
        return 0.0

def get_system_info() -> dict:
    """
    Get current system information
    
    Returns:
        Dictionary with system info
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_total': memory.total / 1024 / 1024 / 1024,  # GB
            'memory_available': memory.available / 1024 / 1024 / 1024,  # GB
            'memory_percent': memory.percent,
            'disk_total': disk.total / 1024 / 1024 / 1024,  # GB
            'disk_free': disk.free / 1024 / 1024 / 1024,  # GB
            'disk_percent': (disk.used / disk.total) * 100
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {}

def optimize_memory():
    """
    Optimize memory usage by cleaning up
    """
    try:
        import gc
        gc.collect()
        logger.info("Memory cleanup completed")
    except Exception as e:
        logger.error(f"Error during memory cleanup: {str(e)}")

def check_system_resources() -> bool:
    """
    Check if system has enough resources
    
    Returns:
        True if resources are sufficient, False otherwise
    """
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check memory (at least 100MB available)
        if memory.available < 100 * 1024 * 1024:
            logger.warning("Low memory available")
            return False
        
        # Check disk space (at least 100MB free)
        if disk.free < 100 * 1024 * 1024:
            logger.warning("Low disk space available")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking system resources: {str(e)}")
        return False

def log_performance_stats():
    """
    Log current performance statistics
    """
    try:
        system_info = get_system_info()
        if system_info:
            logger.info(f"System stats - CPU: {system_info['cpu_percent']:.1f}%, "
                       f"Memory: {system_info['memory_percent']:.1f}%, "
                       f"Disk: {system_info['disk_percent']:.1f}%")
    except Exception as e:
        logger.error(f"Error logging performance stats: {str(e)}")
