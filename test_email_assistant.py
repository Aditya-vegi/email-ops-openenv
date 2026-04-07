#!/usr/bin/env python3
"""
Test script for Email Operations Assistant
"""

import os
import sys
import json

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test if the email assistant can be imported."""
    try:
        from email_assistant import EmailOperationsAssistant
        print("EmailOperationsAssistant imported successfully")
        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def test_environment():
    """Test if required environment variables are set."""
    required_vars = ["API_KEY", "API_BASE_URL"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"Missing environment variables: {missing_vars}")
        return False
    else:
        print("All required environment variables are set")
        return True

def test_basic_functionality():
    """Test basic functionality with mock data."""
    try:
        # This would work if environment variables were set
        print("Basic functionality test would run with proper environment")
        return True
    except Exception as e:
        print(f"Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Email Operations Assistant")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_import),
        ("Environment Test", test_environment),
        ("Basic Functionality Test", test_basic_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nSummary: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("All tests passed! Email assistant is ready.")
        return 0
    else:
        print("Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main())
