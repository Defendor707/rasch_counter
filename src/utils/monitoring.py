"""
Simple monitoring utilities for Rasch Counter Bot
"""
import time
import logging
import psutil
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SimpleMonitor:
    """Simple monitoring class for the bot"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.processed_files = 0
        self.total_students = 0
        
    def increment_request(self):
        """Increment request counter"""
        self.request_count += 1
        
    def increment_error(self):
        """Increment error counter"""
        self.error_count += 1
        
    def increment_processed_files(self, student_count: int = 0):
        """Increment processed files counter"""
        self.processed_files += 1
        self.total_students += student_count
        
    def get_uptime(self) -> float:
        """Get bot uptime in seconds"""
        return time.time() - self.start_time
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        try:
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'uptime_seconds': self.get_uptime(),
                'uptime_hours': self.get_uptime() / 3600,
                'request_count': self.request_count,
                'error_count': self.error_count,
                'error_rate': self.error_count / max(self.request_count, 1) * 100,
                'processed_files': self.processed_files,
                'total_students': self.total_students,
                'memory_usage_mb': memory.used / 1024 / 1024,
                'memory_percent': memory.percent,
                'cpu_percent': cpu_percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            return {}
    
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        if stats:
            logger.info(f"Bot Stats - Uptime: {stats['uptime_hours']:.1f}h, "
                       f"Requests: {stats['request_count']}, "
                       f"Errors: {stats['error_count']}, "
                       f"Files: {stats['processed_files']}, "
                       f"Students: {stats['total_students']}, "
                       f"Memory: {stats['memory_percent']:.1f}%, "
                       f"CPU: {stats['cpu_percent']:.1f}%")

# Global monitor instance
monitor = SimpleMonitor()

def get_health_status() -> Dict[str, Any]:
    """Get health status for health checks"""
    stats = monitor.get_stats()
    
    # Simple health check
    is_healthy = (
        stats.get('error_rate', 0) < 50 and  # Less than 50% error rate
        stats.get('memory_percent', 0) < 90 and  # Less than 90% memory usage
        stats.get('cpu_percent', 0) < 95  # Less than 95% CPU usage
    )
    
    return {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'stats': stats
    }
