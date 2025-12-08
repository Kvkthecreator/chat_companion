#!/usr/bin/env python3
"""
Python Import Test Script - Backend Build Validation
Equivalent to 'npm run build' for Python backend

This script tests all imports in the codebase to catch issues before deployment.
"""

import os
import sys
import importlib
import importlib.util
from pathlib import Path
from typing import List, Tuple, Set

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    directory_path = Path(directory)
    python_files = []
    
    for file_path in directory_path.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" not in str(file_path) and "test_" not in file_path.name:
            python_files.append(file_path)
    
    return python_files

def test_file_compilation(file_path: Path) -> Tuple[bool, str]:
    """Test if a Python file can be compiled (syntax check)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        compile(source, str(file_path), 'exec')
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Compilation error: {e}"

def test_module_import(file_path: Path, project_root: Path) -> Tuple[bool, str]:
    """Test if a module can be imported."""
    try:
        # Convert file path to module name
        relative_path = file_path.relative_to(project_root)
        module_parts = list(relative_path.parts[:-1])  # Remove .py extension
        module_parts.append(relative_path.stem)
        
        # Skip __init__.py files and convert to module path
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]
        
        module_name = ".".join(module_parts)
        
        # Skip if module name is empty or invalid
        if not module_name or module_name.startswith("."):
            return True, "Skipped"
            
        # Try to import the module
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            return False, f"Could not create spec for {module_name}"
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return True, ""
    except ImportError as e:
        return False, f"Import error: {e}"
    except ModuleNotFoundError as e:
        return False, f"Module not found: {e}"
    except Exception as e:
        return False, f"Import error: {e}"

def main():
    """Main test function."""
    print("🔍 Python Backend Import Test")
    print("=" * 50)
    
    # Get project root
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    
    if not src_dir.exists():
        print("❌ src/ directory not found")
        sys.exit(1)
    
    # Add src to Python path for imports
    sys.path.insert(0, str(src_dir))
    
    # Find all Python files
    python_files = find_python_files(str(src_dir))
    print(f"📁 Found {len(python_files)} Python files")
    print()
    
    # Test compilation and imports
    compilation_errors = []
    import_errors = []
    success_count = 0
    
    for file_path in python_files:
        relative_path = file_path.relative_to(src_dir)
        
        # Test compilation
        compilation_ok, compilation_error = test_file_compilation(file_path)
        if not compilation_ok:
            compilation_errors.append((str(relative_path), compilation_error))
            print(f"❌ {relative_path}: Compilation failed")
            continue
            
        # Test imports
        import_ok, import_error = test_module_import(file_path, src_dir)
        if not import_ok:
            import_errors.append((str(relative_path), import_error))
            print(f"⚠️  {relative_path}: Import failed")
            continue
            
        success_count += 1
        print(f"✅ {relative_path}: OK")
    
    # Summary
    print()
    print("📊 Test Summary")
    print("=" * 50)
    print(f"✅ Successful: {success_count}")
    print(f"❌ Compilation errors: {len(compilation_errors)}")
    print(f"⚠️  Import errors: {len(import_errors)}")
    
    # Report errors
    if compilation_errors:
        print()
        print("🚨 Compilation Errors:")
        for file_path, error in compilation_errors:
            print(f"  • {file_path}: {error}")
    
    if import_errors:
        print()
        print("⚠️  Import Errors:")
        for file_path, error in import_errors:
            print(f"  • {file_path}: {error}")
    
    # Exit with error code if there are issues
    total_errors = len(compilation_errors) + len(import_errors)
    if total_errors > 0:
        print(f"\n❌ Build test failed with {total_errors} errors")
        sys.exit(1)
    else:
        print(f"\n🎉 Build test passed! All {success_count} files are importable.")
        sys.exit(0)

if __name__ == "__main__":
    main()