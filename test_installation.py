#!/usr/bin/env python3
"""
Installation Test Script - Verify that the project is properly set up
"""

import sys
import importlib
from pathlib import Path

def test_imports():
    """Test that all modules can be imported"""
    print("🔍 Testing module imports...")
    
    modules_to_test = [
        "config.settings",
        "meegle_sdk",
        "meegle_sdk.auth",
        "meegle_sdk.client", 
        "meegle_sdk.apis",
        "meegle_sdk.models",
        "meegle_business",
        "meegle_business.timeline",
        "meegle_business.export"
    ]
    
    failed_imports = []
    
    for module_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"  ✅ {module_name}")
        except ImportError as e:
            print(f"  ❌ {module_name}: {e}")
            failed_imports.append(module_name)
        except Exception as e:
            print(f"  ⚠️  {module_name}: {e}")
            failed_imports.append(module_name)
    
    return len(failed_imports) == 0, failed_imports

def test_dependencies():
    """Test that required dependencies are available"""
    print("\n🔍 Testing dependencies...")
    
    dependencies = [
        "requests",
        "python-dateutil", 
        "pathlib",
        "json",
        "csv",
        "logging",
        "datetime",
        "dataclasses"
    ]
    
    failed_deps = []
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"  ✅ {dep}")
        except ImportError:
            # Some modules have different import names
            try:
                if dep == "python-dateutil":
                    importlib.import_module("dateutil")
                    print(f"  ✅ {dep} (as dateutil)")
                else:
                    raise
            except ImportError:
                print(f"  ❌ {dep}")
                failed_deps.append(dep)
    
    return len(failed_deps) == 0, failed_deps

def test_project_structure():
    """Test that project structure is correct"""
    print("\n🔍 Testing project structure...")
    
    expected_paths = [
        "config/settings.py",
        "meegle_sdk/__init__.py",
        "meegle_sdk/auth/token_manager.py",
        "meegle_sdk/client/meegle_client.py",
        "meegle_sdk/apis/chart_api.py",
        "meegle_business/__init__.py",
        "meegle_business/timeline/extractor.py",
        "meegle_business/export/csv_exporter.py",
        "examples/sdk_examples.py",
        "examples/business_examples.py",
        "requirements.txt",
        "setup.py",
        "README.md"
    ]
    
    missing_paths = []
    
    for path_str in expected_paths:
        path = Path(path_str)
        if path.exists():
            print(f"  ✅ {path_str}")
        else:
            print(f"  ❌ {path_str}")
            missing_paths.append(path_str)
    
    return len(missing_paths) == 0, missing_paths

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🔍 Testing basic functionality...")
    
    try:
        # Test SDK import and initialization
        from meegle_sdk import MeegleSDK
        print("  ✅ MeegleSDK import")
        
        # Test business layer imports
        from meegle_business import TimelineExtractor, CSVExporter
        print("  ✅ Business layer imports")
        
        # Test model imports
        from meegle_business.timeline.models import TimelineEntry, TimelineData
        print("  ✅ Model imports")
        
        # Test configuration
        from config.settings import get_meegle_config
        config = get_meegle_config()
        print("  ✅ Configuration loading")
        
        return True, []
        
    except Exception as e:
        return False, [str(e)]

def main():
    """Main test function"""
    print("🧪 Meegle Manager Installation Test")
    print("=" * 50)
    
    all_passed = True
    
    # Run tests
    tests = [
        ("Module Imports", test_imports),
        ("Dependencies", test_dependencies), 
        ("Project Structure", test_project_structure),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    for test_name, test_func in tests:
        try:
            passed, failures = test_func()
            if not passed:
                all_passed = False
                print(f"\n❌ {test_name} failed:")
                for failure in failures:
                    print(f"   - {failure}")
        except Exception as e:
            all_passed = False
            print(f"\n❌ {test_name} failed with exception: {e}")
    
    # Final result
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Installation looks good.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and configure your settings")
        print("2. Run: python run_examples.py")
        print("3. Or run individual examples:")
        print("   - python examples/sdk_examples.py")
        print("   - python examples/business_examples.py")
    else:
        print("❌ Some tests failed! Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 