#!/usr/bin/env python3
"""Small regression test for the safe, guarded V5.2 layout patch."""
from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "apply_layout_v5_2.py"
SPEC = importlib.util.spec_from_file_location("apply_layout_v5_2", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_layout_patch_self_test() -> None:
    MODULE.self_test()


if __name__ == "__main__":
    MODULE.self_test()
