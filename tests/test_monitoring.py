"""
Tests for monitoring module
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from utils.monitoring import SimpleMonitor, get_health_status

class TestMonitoring:
    """Monitoring module testlari"""
    
    def test_simple_monitor_initialization(self):
        """Test SimpleMonitor initialization"""
        monitor = SimpleMonitor()
        assert monitor.request_count == 0
        assert monitor.error_count == 0
        assert monitor.processed_files == 0
        assert monitor.total_students == 0
    
    def test_increment_request(self):
        """Test increment request"""
        monitor = SimpleMonitor()
        monitor.increment_request()
        assert monitor.request_count == 1
    
    def test_increment_error(self):
        """Test increment error"""
        monitor = SimpleMonitor()
        monitor.increment_error()
        assert monitor.error_count == 1
    
    def test_increment_processed_files(self):
        """Test increment processed files"""
        monitor = SimpleMonitor()
        monitor.increment_processed_files(10)
        assert monitor.processed_files == 1
        assert monitor.total_students == 10
    
    def test_get_uptime(self):
        """Test get uptime"""
        monitor = SimpleMonitor()
        uptime = monitor.get_uptime()
        assert uptime >= 0
    
    def test_get_stats(self):
        """Test get stats"""
        monitor = SimpleMonitor()
        monitor.increment_request()
        monitor.increment_processed_files(5)
        
        stats = monitor.get_stats()
        assert isinstance(stats, dict)
        assert 'uptime_seconds' in stats
        assert 'request_count' in stats
        assert 'processed_files' in stats
        assert 'total_students' in stats
        assert stats['request_count'] == 1
        assert stats['processed_files'] == 1
        assert stats['total_students'] == 5
    
    def test_log_stats(self):
        """Test log stats"""
        monitor = SimpleMonitor()
        monitor.increment_request()
        # This should not raise an exception
        monitor.log_stats()
    
    def test_get_health_status(self):
        """Test get health status"""
        with patch('utils.monitoring.monitor') as mock_monitor:
            mock_monitor.get_stats.return_value = {
                'error_rate': 10.0,
                'memory_percent': 50.0,
                'cpu_percent': 30.0
            }
            
            status = get_health_status()
            assert isinstance(status, dict)
            assert 'status' in status
            assert 'timestamp' in status
            assert 'stats' in status
    
    def test_get_health_status_unhealthy(self):
        """Test get health status when unhealthy"""
        with patch('utils.monitoring.monitor') as mock_monitor:
            mock_monitor.get_stats.return_value = {
                'error_rate': 60.0,  # High error rate
                'memory_percent': 95.0,  # High memory usage
                'cpu_percent': 30.0
            }
            
            status = get_health_status()
            assert status['status'] == 'unhealthy'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
