#!/usr/bin/env python3
"""
Test runner script for Rasch Counter Bot
Bu script testlarni turli usullarda ishga tushiradi
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=True, coverage=True):
    """Testlarni ishga tushirish"""
    
    # Base command
    cmd = ["python", "-m", "pytest"]
    
    # Test type'ga qarab qo'shimcha parametrlar
    if test_type == "unit":
        cmd.extend(["tests/test_rasch_model.py", "tests/test_real_data.py"])
    elif test_type == "integration":
        cmd.extend(["tests/test_integration.py"])
    elif test_type == "comprehensive":
        cmd.extend(["tests/test_rasch_model_comprehensive.py"])
    elif test_type == "performance":
        cmd.extend(["-m", "performance"])
    elif test_type == "quick":
        cmd.extend(["-m", "not slow"])
    else:  # all
        cmd.extend(["tests/"])
    
    # Verbose mode
    if verbose:
        cmd.append("-v")
    
    # Coverage
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Additional options
    cmd.extend([
        "--tb=short",
        "--disable-warnings"
    ])
    
    print(f"🚀 Running tests: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("❌ pytest not found. Please install it: pip install pytest")
        return False

def run_specific_test(test_file, test_function=None):
    """Muayyan test faylini ishga tushirish"""
    cmd = ["python", "-m", "pytest", test_file, "-v"]
    
    if test_function:
        cmd.extend(["-k", test_function])
    
    print(f"🎯 Running specific test: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print("\n✅ Test passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with exit code {e.returncode}")
        return False

def run_coverage_report():
    """Coverage hisobotini ko'rsatish"""
    cmd = ["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=html"]
    
    print("📊 Generating coverage report...")
    subprocess.run(cmd)
    
    print("\n📈 Coverage report generated in htmlcov/index.html")

def run_benchmark():
    """Performance benchmark ishga tushirish"""
    cmd = ["python", "-m", "pytest", "tests/", "-m", "performance", "-v", "--benchmark-only"]
    
    print("⚡ Running performance benchmarks...")
    subprocess.run(cmd)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Rasch Counter Bot Test Runner")
    parser.add_argument("--type", choices=["all", "unit", "integration", "comprehensive", "performance", "quick"], 
                       default="all", help="Test type to run")
    parser.add_argument("--file", help="Specific test file to run")
    parser.add_argument("--function", help="Specific test function to run")
    parser.add_argument("--no-coverage", action="store_true", help="Disable coverage reporting")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode")
    parser.add_argument("--coverage-only", action="store_true", help="Only run coverage report")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")
    
    args = parser.parse_args()
    
    print("🧪 Rasch Counter Bot Test Runner")
    print("=" * 50)
    
    # Coverage only
    if args.coverage_only:
        run_coverage_report()
        return
    
    # Benchmark only
    if args.benchmark:
        run_benchmark()
        return
    
    # Specific test file
    if args.file:
        success = run_specific_test(args.file, args.function)
        sys.exit(0 if success else 1)
    
    # Run tests
    success = run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=not args.no_coverage
    )
    
    if success:
        print("\n🎉 All tests completed successfully!")
        if not args.no_coverage:
            print("📊 Check htmlcov/index.html for coverage report")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
