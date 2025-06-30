#!/usr/bin/env python3
"""
Run Examples Script - Quick way to test the project
"""

import sys
import subprocess
from pathlib import Path

def run_sdk_examples():
    """Run SDK examples"""
    print("🚀 Running SDK Examples...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "examples/sdk_examples.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run SDK examples: {e}")
        return False

def run_business_examples():
    """Run business layer examples"""
    print("\n🚀 Running Business Layer Examples...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "examples/business_examples.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Failed to run business examples: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Meegle Manager - Example Runner")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("   Please copy .env.example to .env and configure your settings.")
        print()
    
    # Check which examples to run
    if len(sys.argv) > 1 and sys.argv[1] == "business":
        success = run_business_examples()
    elif len(sys.argv) > 1 and sys.argv[1] == "sdk":
        success = run_sdk_examples()
    else:
        # Run both
        sdk_success = run_sdk_examples()
        business_success = run_business_examples()
        success = sdk_success and business_success
    
    if success:
        print("\n✅ All examples completed successfully!")
    else:
        print("\n❌ Some examples failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 