#!/usr/bin/env python3
"""Slice-5 rescore: transcript cells computed on POST-FORK content only.

For each lineage's final transcript, find the FIRST compact_boundary record (the fork
point — everything after it is successor behavior) and slice from there; disk cells are
unchanged (fork-manifest delta). Writes scoring_sliced/<proj>/<lid>.json."""
import json, os, subprocess, sys, tempfile

RUN = os.path.dirname(os.path.abspath(__file__))

def slice_transcript(src, dst):
    lines = open(src, errors="replace").readlines()
    cut = 0
    for i, line in enumerate(lines):
        if '"compact_boundary"' in line:
            cut = i
            break
    with open(dst, "w") as f:
        f.writelines(lines[cut:])
    return cut, len(lines)

def main():
    for proj in ("p1", "p2", "p3"):
        st = json.load(open(os.path.join(RUN, f"state_{proj}_lineages.json")))["lineages"]
        outdir = os.path.join(RUN, "scoring_sliced", proj)
        os.makedirs(outdir, exist_ok=True)
        for lid, lin in sorted(st.items()):
            src = os.path.join(RUN, "transcripts", f"{proj}_final_{lid}_{lin['sid']}.jsonl")
            with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as tf:
                sliced = tf.name
            cut, total = slice_transcript(src, sliced)
            out = subprocess.run(
                ["python3", os.path.join(RUN, "..", "score_arm.py"),
                 "--workspace", lin["ws"], "--transcript", sliced,
                 "--config", os.path.join(RUN, "..", f"scorer_config_{proj}.json")],
                capture_output=True, text=True)
            os.unlink(sliced)
            if out.returncode != 0:
                print(proj, lid, "ERROR", out.stderr[-150:]); continue
            v = json.loads(out.stdout)
            v["slice"] = {"cut_line": cut, "total_lines": total}
            json.dump(v, open(os.path.join(outdir, f"{lid}.json"), "w"), indent=2)
        print(proj, "rescored")

if __name__ == "__main__":
    main()
