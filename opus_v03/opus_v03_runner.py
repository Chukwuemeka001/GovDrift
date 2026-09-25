#!/usr/bin/env python3
"""Opus v0.3 check: the frozen Tier-2 runner with Opus registered, a chosen frozen plugin snapshot, and a TRULY lazy
owner (never confirms anything). Same wrapper drives the base scenario and the long-context extension.

  python3 opus_v03_runner.py --plugin v02|v03 <scenario.json> --out DIR --runs native:opus:1,plugin-lazy:opus:1
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
which = sys.argv[sys.argv.index("--plugin") + 1]
del sys.argv[sys.argv.index("--plugin"):sys.argv.index("--plugin") + 2]
import runner  # noqa: E402
runner.PLUGIN = os.path.join(os.path.dirname(HERE), f"plugin_{which}")
sys.path.insert(0, runner.PLUGIN)
runner.MODELS["opus"] = "claude-opus-5-5"
runner.PRICE["opus"] = (0.0, 0.0, 0.0, 0.0)

_run_init = runner.Run.__init__
def _run(self, *a, **k):
    _run_init(self, *a, **k)
    self.sc["lazy_owner_turns"] = []          # never confirms: the v0.3 design condition
runner.Run.__init__ = _run

_lin_init = runner.Lineage.__init__
def _lin(self, *a, **k):                      # as opus_ext_runner: N2 must be a NEW session, not N1's
    _lin_init(self, *a, **k)
    if "N1" in self.st["log"] and "N2" not in self.st["log"] and self.st.get("sid2") and "sid2_n1" not in self.st:
        self.st["sid2_n1"], self.st["sid2"] = self.st["sid2"], None
        self.save()
runner.Lineage.__init__ = _lin

if __name__ == "__main__":
    runner.main()
