#!/usr/bin/env python3
"""Relaunch the Haiku ablation arm (D5): stdin explicitly closed so `claude -p` cannot read stray piped input."""
import os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["none", "verbatim", "flat", "status", "full"]
for s in range(1, 11):
    k = (s - 1) % 5
    runs = ",".join(f"abl-{a}:haiku:{s}" for a in ARMS[k:] + ARMS[:k])
    subprocess.Popen(["python3", "ablation_runner.py", "scenarios/nclex_remediation.json", "--out", "results/ablation",
                      "--runs", runs, "--kill", "12"], cwd=HERE, stdin=subprocess.DEVNULL,
                     stdout=open(os.path.join(HERE, f"results/ablation/log_h_s{s}.txt"), "w"), stderr=subprocess.STDOUT,
                     start_new_session=True)
    print(s, runs)
