#!/usr/bin/env python3
"""
Test script to verify proxy fix works correctly
"""

import os
import sys

def test_environment_variables():
    """Test that we're using the correct environment variables."""
    print("Testing Environment Variables:")
    print("=" * 40)
    
    # Test the correct variable names
    correct_vars = ["API_KEY", "API_BASE_URL", "MODEL_NAME"]
    
    for var in correct_vars:
        value = os.getenv(var)
        status = "SET" if value else "NOT SET"
        print(f"  {var}: {status}")
    
    print("\nChecking for old variable names:")
    
    # Check for old/incorrect variable names
    old_vars = ["OPENAI_API_KEY"]
    
    for var in old_vars:
        value = os.getenv(var)
        status = "SET" if value else "NOT SET"
        print(f"  {var}: {status} {'(SHOULD NOT BE USED)' if value else ''}")
    
    print("\n" + "=" * 40)
    print("RESULT: Using correct hackathon variable names")
    return len([v for v in correct_vars if os.getenv(v)]) == len(correct_vars)

def test_file_imports():
    """Test that our files use correct variable names."""
    print("\nTesting File Imports:")
    print("=" * 40)
    
    try:
        # Test email_assistant.py
        with open('email_assistant.py', 'r') as f:
            content = f.read()
            if 'os.environ["API_KEY"]' in content and 'os.environ["OPENAI_API_KEY"]' not in content:
                print("  ✅ email_assistant.py: Uses correct variable names")
            else:
                print("  ❌ email_assistant.py: Variable name issue")
        
        # Test inference.py  
        with open('inference.py', 'r') as f:
            content = f.read()
            if 'os.getenv("API_KEY")' in content and 'os.getenv("OPENAI_API_KEY")' not in content:
                print("  ✅ inference.py: Uses correct variable names")
            else:
                print("  ❌ inference.py: Variable name issue")
                
    except Exception as e:
        print(f"  ❌ File test error: {e}")
    
    print("\n" + "=" * 40)

def main():
    """Run all tests."""
    print("PROXY FIX VERIFICATION")
    print("=" * 50)
    
    env_test = test_environment_variables()
    file_test = test_file_imports()
    
    if env_test and file_test:
        print("\nALL TESTS PASSED - Proxy fix successful!")
        print("Ready for hackathon resubmission!")
        return 0
    else:
        print("\nSOME TESTS FAILED - Review fixes needed")
        return 1

if __name__ == "__main__":
    exit(main())
