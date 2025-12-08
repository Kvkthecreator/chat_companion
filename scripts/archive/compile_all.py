"""Fail the build if *any* .py file has an unresolved import."""
import compileall, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1] / "api" / "src"
ok = compileall.compile_dir(root, quiet=1, force=True)
sys.exit(0 if ok else 1)
