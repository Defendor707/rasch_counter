"""
Tests for performance utilities
"""
import pytest
import time
import psutil
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from utils.performance import (
    monitor_performance, get_cpu_load, get_system_info
)

class TestPerformance:
    """Performance utilities testlari"""
    
    def test_get_cpu_load_success(self):
        """CPU load success test"""
        with patch('builtins.open', mock_open(read_data="1.5 1.2 1.0 2/100 12345")):
            load = get_cpu_load()
            assert load == 1.5
    
    def test_get_cpu_load_file_not_found(self):
        """CPU load file not found test"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            load = get_cpu_load()
            assert load == 0.0
    
    def test_get_cpu_load_invalid_data(self):
        """CPU load invalid data test"""
        with patch('builtins.open', mock_open(read_data="invalid data")):
            load = get_cpu_load()
            assert load == 0.0
    
    def test_get_system_info_success(self):
        """System info success test"""
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock memory info
            mock_memory.return_value = MagicMock(
                total=8 * 1024**3,  # 8GB
                used=4 * 1024**3,   # 4GB
                percent=50.0
            )
            
            # Mock disk info
            mock_disk.return_value = MagicMock(
                total=100 * 1024**3,  # 100GB
                used=50 * 1024**3,    # 50GB
                percent=50.0
            )
            
            info = get_system_info()
            
            assert 'cpu_percent' in info
            # Check that we have some memory and disk info
            assert 'memory_percent' in info
            assert 'disk_percent' in info
            # Check that the values are reasonable
            assert info['cpu_percent'] == 50.0
            assert info['memory_percent'] == 50.0
            assert info['disk_percent'] == 50.0
    
    def test_get_system_info_error(self):
        """System info error test"""
        with patch('psutil.cpu_percent', side_effect=Exception("Test error")):
            info = get_system_info()
            assert info == {}
    
    def test_monitor_performance_success(self):
        """Monitor performance success test"""
        @monitor_performance
        def test_function():
            time.sleep(0.01)  # Small delay
            return "success"
        
        with patch('psutil.Process') as mock_process:
            # Mock memory info
            mock_memory = MagicMock()
            mock_memory.rss = 100 * 1024 * 1024  # 100MB
            mock_process.return_value.memory_info.return_value = mock_memory
            
            result = test_function()
            assert result == "success"
    
    def test_monitor_performance_error(self):
        """Monitor performance error test"""
        @monitor_performance
        def test_function():
            raise ValueError("Test error")
        
        with patch('psutil.Process') as mock_process:
            # Mock memory info
            mock_memory = MagicMock()
            mock_memory.rss = 100 * 1024 * 1024  # 100MB
            mock_process.return_value.memory_info.return_value = mock_memory
            
            with pytest.raises(ValueError, match="Test error"):
                test_function()
    
    def test_monitor_performance_with_args(self):
        """Monitor performance with arguments test"""
        @monitor_performance
        def test_function_with_args(x, y):
            return x + y
        
        with patch('psutil.Process') as mock_process:
            # Mock memory info
            mock_memory = MagicMock()
            mock_memory.rss = 100 * 1024 * 1024  # 100MB
            mock_process.return_value.memory_info.return_value = mock_memory
            
            result = test_function_with_args(2, 3)
            assert result == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
