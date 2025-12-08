#!/usr/bin/env python3
"""
Test script to verify requirements installation works correctly.
Use this to debug Render deployment package issues.
"""

import sys
import subprocess

def test_package_imports():
    """Test that all critical packages can be imported."""
    print("🔍 Testing package imports...")
    
    critical_packages = [
        "databases",
        "asyncpg", 
        "fastapi",
        "uvicorn",
        "pydantic"
    ]
    
    failed_imports = []
    
    for package in critical_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError as e:
            print(f"  ✗ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n❌ FAILED IMPORTS: {failed_imports}")
        print("\n🔧 To fix, run:")
        print(f"pip install {' '.join(failed_imports)}")
        return False
    
    print("\n✅ All critical packages imported successfully!")
    return True

def test_databases_specifically():
    """Test the databases package specifically since that's the main issue."""
    print("\n🔍 Testing databases package specifically...")
    
    try:
        from databases import Database
        print("  ✓ databases.Database imported")
        
        # Test creating a database instance
        db = Database("sqlite:///test.db")
        print("  ✓ Database instance created")
        
        # Check if postgresql extras are available
        try:
            import asyncpg
            print("  ✓ asyncpg (postgresql driver) available")
        except ImportError:
            print("  ⚠️  asyncpg not available - postgresql support may be limited")
        
        return True
        
    except ImportError as e:
        print(f"  ✗ databases import failed: {e}")
        print("\n🔧 To fix databases package:")
        print("pip install 'databases[postgresql]>=0.7.0'")
        print("pip install 'asyncpg>=0.29.0'")
        return False

def check_pip_list():
    """Show what packages are actually installed."""
    print("\n📦 Checking installed packages...")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True, timeout=10)
        
        lines = result.stdout.split('\n')
        relevant_packages = [
            line for line in lines 
            if any(pkg in line.lower() for pkg in ['databases', 'asyncpg', 'fastapi', 'pydantic'])
        ]
        
        if relevant_packages:
            print("  Relevant packages found:")
            for line in relevant_packages:
                print(f"    {line}")
        else:
            print("  ⚠️  No relevant packages found in pip list")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Failed to get pip list: {e}")
        return False

def test_requirements_file():
    """Check if requirements.txt is readable and contains databases."""
    print("\n📄 Checking requirements.txt...")
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        if "databases" in content:
            print("  ✓ 'databases' found in requirements.txt")
        else:
            print("  ✗ 'databases' NOT found in requirements.txt")
            
        if "asyncpg" in content:
            print("  ✓ 'asyncpg' found in requirements.txt")
        else:
            print("  ✗ 'asyncpg' NOT found in requirements.txt")
            
        # Show first few lines
        lines = content.split('\n')[:10]
        print("  First 10 lines of requirements.txt:")
        for i, line in enumerate(lines, 1):
            if line.strip():
                print(f"    {i:2}: {line}")
                
        return True
        
    except FileNotFoundError:
        print("  ✗ requirements.txt not found")
        return False
    except Exception as e:
        print(f"  ✗ Error reading requirements.txt: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Requirements Installation Test")
    print("=" * 50)
    
    results = []
    results.append(test_requirements_file())
    results.append(check_pip_list())
    results.append(test_package_imports())
    results.append(test_databases_specifically())
    
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ Requirements should work for Render deployment!")
        sys.exit(0)
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("🔧 Fix the issues above before deploying to Render")
        sys.exit(1)

if __name__ == "__main__":
    main()