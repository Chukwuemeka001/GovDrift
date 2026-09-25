#!/usr/bin/env python3
"""Tier 2c-ext: continue the Tier-2c Opus lineages to a realistic long context (~250k) and compact a third time.
Wraps the frozen runner; only (1) registers Opus and (2) parks the earlier fresh-session id so N2 is a NEW session."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runner  # noqa: E402

runner.MODELS["opus"] = "claude-opus-5-5"
runner.PRICE["opus"] = (0.0, 0.0, 0.0, 0.0)

_orig_init = runner.Lineage.__init__
def _init(self, *a, **k):
    _orig_init(self, *a, **k)
    if "N2" not in self.st["log"] and self.st.get("sid2") and "sid2_n1" not in self.st:
        self.st["sid2_n1"], self.st["sid2"] = self.st["sid2"], None
        self.save()
runner.Lineage.__init__ = _init

if __name__ == "__main__":
    runner.main()
