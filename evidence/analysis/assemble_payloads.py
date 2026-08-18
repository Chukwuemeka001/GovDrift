#!/usr/bin/env python3
"""Assemble per-arm first-post-fork payload files for one project+generation.

Usage:
  assemble_payloads.py --project p1 --gen 1 --tokens 118000 --transcript <abs path>
                       [--generation-note "..."]

Reads:  GovDrift/BANNER_V2_TEMPLATE.md, payloads/<proj>/gen<g>/ledger_B.md,
        ledger_D.md, filler_C_base.md
Writes: payloads/<proj>/gen<g>/B.txt, D.txt, C.txt  (arm A gets no payload)
C is token-matched to B within ±5% by trimming filler paragraphs from the end.
Token estimate = chars/4 (recorded; both counts printed and saved to payload_manifest).
"""
import argparse, json, os

RUN = os.path.dirname(os.path.abspath(__file__))
BANNER = "/Users/emeka/GovDrift/BANNER_V2_TEMPLATE.md"

def toks(s): return len(s) // 4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--gen", required=True)
    ap.add_argument("--tokens", required=True, help="human-readable compaction size, e.g. 118,000")
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--generation-note", default="This was the session's first compaction.")
    args = ap.parse_args()

    d = os.path.join(RUN, "payloads", args.project, f"gen{args.gen}")
    banner = open(BANNER).read()
    banner = (banner.replace("{TOKENS}", args.tokens)
                    .replace("{GENERATION_NOTE}", args.generation_note)
                    .replace("{TRANSCRIPT_PATH}", args.transcript))

    ledger_b = open(os.path.join(d, "ledger_B.md")).read()
    ledger_d = open(os.path.join(d, "ledger_D.md")).read()
    b = banner + "\n" + ledger_b
    dd = banner + "\n" + ledger_d

    filler = open(os.path.join(d, "filler_C_base.md")).read()
    filler = filler.replace("{TOKENS}", args.tokens)
    target = len(b)
    paras = filler.split("\n\n")
    while len("\n\n".join(paras)) > target * 1.05 and len(paras) > 2:
        paras.pop()
    c = "\n\n".join(paras)
    if len(c) < target * 0.95:
        pad = ("\n\n## Note\nThe recap above reflects the state of the workspace at the "
               "time of compaction; consult the files themselves for current detail.")
        while len(c) < target * 0.95:
            c += pad
    open(os.path.join(d, "B.txt"), "w").write(b)
    open(os.path.join(d, "D.txt"), "w").write(dd)
    open(os.path.join(d, "C.txt"), "w").write(c)

    manifest = {
        "project": args.project, "gen": args.gen, "compaction_tokens": args.tokens,
        "transcript_pointer": args.transcript,
        "token_estimates_chars_div_4": {"B": toks(b), "C": toks(c), "D": toks(dd)},
        "C_within_5pct_of_B": abs(toks(c) - toks(b)) <= 0.05 * toks(b),
        "D_within_5pct_of_B": abs(toks(dd) - toks(b)) <= 0.05 * toks(b),
    }
    json.dump(manifest, open(os.path.join(d, "payload_manifest.json"), "w"), indent=2)
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
