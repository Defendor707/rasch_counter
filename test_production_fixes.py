#!/usr/bin/env python3
"""
Production fixes test fayli
Katta fayllar bilan ishlashni test qilish
"""

import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path

# Add src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from utils.production_fixes import (
    detect_environment,
    get_optimal_workers,
    get_optimal_chunk_size,
    safe_rasch_calculation
)
from models.rasch_model import rasch_model
from data_processing.data_processor import process_exam_data

def create_test_data(n_students=2000, n_questions=50):
    """Test ma'lumotlari yaratish"""
    print(f"Creating test data: {n_students} students, {n_questions} questions")
    
    # Random student responses
    np.random.seed(42)
    data = np.random.binomial(1, 0.6, (n_students, n_questions))
    
    # Student names
    student_names = [f"Student_{i+1:04d}" for i in range(n_students)]
    
    # Question columns
    question_cols = [f"Q{i+1:02d}" for i in range(n_questions)]
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=question_cols)
    df.insert(0, 'Student', student_names)
    
    return df

def test_environment_detection():
    """Environment detection test"""
    print("\n=== Environment Detection Test ===")
    env = detect_environment()
    print(f"Detected environment: {env}")
    
    workers = get_optimal_workers()
    print(f"Optimal workers: {workers}")
    
    chunk_size = get_optimal_chunk_size(2000)
    print(f"Optimal chunk size for 2000 students: {chunk_size}")

def test_safe_rasch_calculation():
    """Safe Rasch calculation test"""
    print("\n=== Safe Rasch Calculation Test ===")
    
    # Small data test
    small_data = np.random.binomial(1, 0.6, (100, 20))
    print("Testing small data (100 students, 20 questions)...")
    
    try:
        theta, beta = safe_rasch_calculation(small_data)
        print(f"✓ Small data success: theta shape {theta.shape}, beta shape {beta.shape}")
        print(f"  Theta range: [{theta.min():.3f}, {theta.max():.3f}]")
        print(f"  Beta range: [{beta.min():.3f}, {beta.max():.3f}]")
    except Exception as e:
        print(f"✗ Small data failed: {str(e)}")
    
    # Large data test
    large_data = np.random.binomial(1, 0.6, (1500, 30))
    print("\nTesting large data (1500 students, 30 questions)...")
    
    try:
        theta, beta = safe_rasch_calculation(large_data)
        print(f"✓ Large data success: theta shape {theta.shape}, beta shape {beta.shape}")
        print(f"  Theta range: [{theta.min():.3f}, {theta.max():.3f}]")
        print(f"  Beta range: [{beta.min():.3f}, {beta.max():.3f}]")
    except Exception as e:
        print(f"✗ Large data failed: {str(e)}")

def test_full_processing():
    """Full processing test"""
    print("\n=== Full Processing Test ===")
    
    # Create test data
    df = create_test_data(1000, 40)
    print(f"Created test data: {df.shape}")
    
    try:
        # Process data
        results = process_exam_data(df)
        print("✓ Full processing success!")
        
        # Check results
        if len(results) >= 4:
            results_df, ability_estimates, grade_counts, original_df = results[:4]
            print(f"  Results DataFrame shape: {results_df.shape}")
            print(f"  Ability estimates shape: {ability_estimates.shape}")
            print(f"  Grade counts: {grade_counts}")
        else:
            print("  Unexpected results format")
            
    except Exception as e:
        print(f"✗ Full processing failed: {str(e)}")
        import traceback
        traceback.print_exc()

def test_memory_usage():
    """Memory usage test"""
    print("\n=== Memory Usage Test ===")
    
    import psutil
    process = psutil.Process()
    
    # Initial memory
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Initial memory usage: {initial_memory:.1f} MB")
    
    # Test with different data sizes
    for n_students in [500, 1000, 1500]:
        print(f"\nTesting with {n_students} students...")
        
        df = create_test_data(n_students, 30)
        
        try:
            results = process_exam_data(df)
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_used = memory_after - initial_memory
            
            print(f"  Memory used: {memory_used:.1f} MB")
            print(f"  Total memory: {memory_after:.1f} MB")
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")

def main():
    """Main test function"""
    print("Production Fixes Test Suite")
    print("=" * 50)
    
    # Set environment to test
    os.environ['ENVIRONMENT'] = 'test'
    
    try:
        test_environment_detection()
        test_safe_rasch_calculation()
        test_full_processing()
        test_memory_usage()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed!")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
