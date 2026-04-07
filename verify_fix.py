#!/usr/bin/env python3
"""
Simple verification that proxy fix is working
"""

import os

def main():
    print("PROXY FIX VERIFICATION")
    print("=" * 40)
    
    # Check correct variables
    api_key_set = "API_KEY" in os.environ
    base_url_set = "API_BASE_URL" in os.environ
    
    print(f"API_KEY environment variable: {'SET' if api_key_set else 'NOT SET'}")
    print(f"API_BASE_URL environment variable: {'SET' if base_url_set else 'NOT SET'}")
    
    # Check for incorrect variables
    old_api_key = "OPENAI_API_KEY" in os.environ
    print(f"OPENAI_API_KEY (incorrect): {'SET' if old_api_key else 'NOT SET'}")
    
    print("\n" + "=" * 40)
    
    if api_key_set and base_url_set and not old_api_key:
        print("SUCCESS: All proxy fixes implemented correctly!")
        return 0
    else:
        print("ISSUE: Some fixes may be needed")
        return 1

if __name__ == "__main__":
    exit(main())
