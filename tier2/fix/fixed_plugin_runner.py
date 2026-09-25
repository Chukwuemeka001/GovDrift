#!/usr/bin/env python3
"""Tier 2-fix: the frozen Tier-2 runner, pointed at the FIXED release plugin (~/drift-ledger/plugin)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner  # noqa: E402
runner.PLUGIN = os.path.expanduser("~/drift-ledger/plugin")
sys.path.insert(0, runner.PLUGIN)
if __name__ == "__main__":
    runner.main()
