"""Runs every test without needing pytest:  python -m tests.run_all   (pytest also works: python -m pytest -q)"""
import importlib
import pathlib
import sys
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
passed = failed = 0
for path in sorted(pathlib.Path(__file__).parent.glob("test_*.py")):
    mod = importlib.import_module(f"tests.{path.stem}")
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        try:
            getattr(mod, name)()
            passed += 1
            print(f"PASS  {path.stem}::{name}")
        except Exception:
            failed += 1
            print(f"FAIL  {path.stem}::{name}")
            traceback.print_exc()
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
