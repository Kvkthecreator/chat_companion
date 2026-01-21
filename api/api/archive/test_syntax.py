#!/usr/bin/env python3
"""
Python Syntax and Import Path Test - Backend Build Validation
Lighter version that tests syntax and import paths without requiring dependencies

This focuses on catching the types of errors we've been seeing in Render deployments.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Tuple, Set, Dict

def find_python_files(directory: str) -> List[Path]:
    """Find all Python files in the directory."""
    directory_path = Path(directory)
    python_files = []
    
    for file_path in directory_path.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" not in str(file_path) and "test_" not in file_path.name:
            python_files.append(file_path)
    
    return python_files

def test_syntax(file_path: Path) -> Tuple[bool, str]:
    """Test if a Python file has valid syntax."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        ast.parse(source, str(file_path))
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error on line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Parse error: {e}"

def extract_imports(file_path: Path) -> Tuple[List[str], List[str]]:
    """Extract import statements from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        imports = []
        from_imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                from_imports.append(module)
        
        return imports, from_imports
    except Exception as e:
        return [], []

def check_relative_imports(file_path: Path, project_root: Path) -> List[str]:
    """Check for problematic relative import patterns."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for the specific patterns that were causing issues
            if line.startswith("from ") and "schemas" in line:
                if "....schemas" in line:
                    issues.append(f"Line {i}: Four-dot relative import may cause deployment issues: {line}")
                elif "...schemas" in line and "src.schemas" not in line:
                    issues.append(f"Line {i}: Three-dot relative import may cause deployment issues: {line}")
                elif "..schemas" in line and "src.schemas" not in line:
                    issues.append(f"Line {i}: Two-dot relative import may cause deployment issues: {line}")
        
        return issues
    except Exception:
        return []

def check_file_structure(src_dir: Path) -> Dict[str, bool]:
    """Check if expected directories/files exist."""
    checks = {
        "schemas directory": (src_dir / "schemas").exists(),
        "app directory": (src_dir / "app").exists(),
        "context_composition_schema": (src_dir / "schemas" / "context_composition_schema.py").exists(),
        "document_composition_schema": (src_dir / "schemas" / "document_composition_schema.py").exists(),
        "basket_intelligence_schema": (src_dir / "schemas" / "basket_intelligence_schema.py").exists(),
    }
    return checks

def main():
    """Main test function."""
    print("🔍 Python Backend Syntax & Import Path Test")
    print("=" * 60)
    
    # Get project root
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    
    if not src_dir.exists():
        print("❌ src/ directory not found")
        sys.exit(1)
    
    # Check file structure
    print("📁 Checking project structure...")
    structure_checks = check_file_structure(src_dir)
    for check_name, exists in structure_checks.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {check_name}")
    
    missing_structure = [name for name, exists in structure_checks.items() if not exists]
    if missing_structure:
        print(f"\n⚠️  Missing: {', '.join(missing_structure)}")
    
    print()
    
    # Find all Python files
    python_files = find_python_files(str(src_dir))
    print(f"📄 Found {len(python_files)} Python files")
    print()
    
    # Test syntax and imports
    syntax_errors = []
    import_issues = []
    success_count = 0
    
    for file_path in python_files:
        relative_path = file_path.relative_to(src_dir)
        
        # Test syntax
        syntax_ok, syntax_error = test_syntax(file_path)
        if not syntax_ok:
            syntax_errors.append((str(relative_path), syntax_error))
            print(f"❌ {relative_path}: Syntax error")
            continue
        
        # Check for problematic import patterns
        import_problems = check_relative_imports(file_path, src_dir)
        if import_problems:
            import_issues.extend([(str(relative_path), issue) for issue in import_problems])
            print(f"⚠️  {relative_path}: Import path issues")
            continue
        
        success_count += 1
        print(f"✅ {relative_path}: OK")
    
    # Summary
    print()
    print("📊 Test Summary")
    print("=" * 60)
    print(f"✅ Files with valid syntax and imports: {success_count}")
    print(f"❌ Syntax errors: {len(syntax_errors)}")
    print(f"⚠️  Import path issues: {len(import_issues)}")
    
    # Report errors
    if syntax_errors:
        print()
        print("🚨 Syntax Errors:")
        for file_path, error in syntax_errors:
            print(f"  • {file_path}: {error}")
    
    if import_issues:
        print()
        print("⚠️  Import Path Issues:")
        for file_path, issue in import_issues:
            print(f"  • {file_path}: {issue}")
    
    # Exit with error code if there are critical issues
    critical_errors = len(syntax_errors) + len(import_issues)
    if critical_errors > 0:
        print(f"\n❌ Build test failed with {critical_errors} critical issues")
        print("These issues will likely cause deployment failures on Render")
        sys.exit(1)
    else:
        print(f"\n🎉 Build test passed! All {success_count} files have valid syntax and import paths.")
        print("✅ Ready for deployment")
        sys.exit(0)

if __name__ == "__main__":
    main()