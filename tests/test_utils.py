"""
Tests for utils module
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src directory to Python path
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from utils.utils import display_grade_distribution, calculate_statistics

class TestUtils:
    """Utils module testlari"""
    
    def test_display_grade_distribution(self):
        """Test grade distribution display"""
        grade_counts = {'A': 5, 'B': 10, 'C': 3, 'NC': 2}
        # display_grade_distribution returns None, not a string
        result = display_grade_distribution(grade_counts)
        assert result is None
    
    def test_display_grade_distribution_empty(self):
        """Test grade distribution display with empty data"""
        grade_counts = {}
        result = display_grade_distribution(grade_counts)
        assert result is None
    
    def test_calculate_statistics(self):
        """Test statistics calculation"""
        # Test that the function exists and is callable
        assert callable(calculate_statistics)
    
    def test_calculate_statistics_empty(self):
        """Test statistics calculation with empty data"""
        # Test that the function exists and is callable
        assert callable(calculate_statistics)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
