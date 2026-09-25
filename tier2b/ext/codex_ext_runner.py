#!/usr/bin/env python3
"""Tier 2b-ext: continue the Tier-2b GPT-6-Sol lineages to ~220k live context (~85% of Sol's 258k window), compact a
third time, then the long-context probes. Wraps codex_runner unchanged except for parking the earlier fresh-session id
so N2 is a NEW session."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import codex_runner  # noqa: E402

_orig = codex_runner.CodexLineage.__init__
def _init(self, *a, **k):
    _orig(self, *a, **k)
    if "N2" not in self.st["log"] and self.st.get("sid2") and "sid2_n1" not in self.st:
        self.st["sid2_n1"], self.st["sid2"] = self.st["sid2"], None
        self.save()
codex_runner.CodexLineage.__init__ = _init

if __name__ == "__main__":
    codex_runner.main()
