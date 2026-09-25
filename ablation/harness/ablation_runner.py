#!/usr/bin/env python3
"""M2 ablation runner (S5) — Claude Code. Wraps runner.py without modifying it.

  python3 ablation_runner.py <scenario.json> --out <dir> --runs abl-verbatim:haiku:1,abl-none:haiku:1 [--kill 40] [--dry]

Every arm loads the SAME plugin (plugin_ablation) with per-lineage env: DRIFTLEDGER_PACKET_MODE=<arm>, GATES=off,
REMINDER=off, VERBATIM_FILE, DRIFTLEDGER_HOME. No owner commands and no capture reminder in transcripts: the controller
seeds the ground truth out of band via the plugin_ablation CLI (owner authority, fixture.py texts) after each governing
turn. X1 (second harness) is skipped. Fail-stops: store check before compact1; injection check after each compact.

Choices (logged in state["choices"]):
- L9 exception is seeded AND consumed right after T10 (fixture order).
- VERBATIM_FILE is a per-lineage progressive copy of nclex_verbatim.json (only messages of governing turns already
  seeded), so the verbatim arm cannot inject not-yet-spoken owner messages at T1 startup / subagent starts. At compact1
  it is identical to nclex_verbatim.json.
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ABL = os.path.join(ROOT, "plugin_ablation")
sys.path.insert(0, HERE)
import runner  # noqa: E402
sys.path.insert(0, ABL)                                   # driftledger must resolve to plugin_ablation, not the frozen plugin
sys.path.insert(0, os.path.join(ROOT, "plugin_ablation_tests"))
import fixture  # noqa: E402

ARMS = {"abl-none": "none", "abl-verbatim": "verbatim", "abl-flat": "flat", "abl-status": "status", "abl-full": "full"}
GOV_TURNS = [1, 2, 3, 5, 6, 7, 9, 10, 11]                # turn of each nclex_verbatim.json message, in order
VERBATIM_ALL = json.load(open(fixture.VERBATIM))
assert len(VERBATIM_ALL) == len(GOV_TURNS)
CHOICES = ["L9 exception seeded and CONSUMED right after T10",
           "X1 (second harness) skipped for all arms",
           "VERBATIM_FILE = per-lineage progressive copy of nclex_verbatim.json (full list once T11 is seeded)",
           "careful_owner disabled; no /drift-ledger: prompts; REMINDER=off; GATES=off"]


def check_driftledger():
    import driftledger
    assert os.path.realpath(driftledger.__file__).startswith(os.path.realpath(ABL)), driftledger.__file__


class AblMixin:
    """Shared by the Claude and Codex ablation lineages."""
    def abl_init(self):
        if self.arm not in ARMS: raise SystemExit(f"unknown arm {self.arm}")
        self.mode = ARMS[self.arm]
        self.vfile = os.path.join(self.base, "verbatim.json")
        if not os.path.exists(self.vfile): self.write_verbatim(0)
        self.st.setdefault("choices", CHOICES); self.st.setdefault("inject", {}); self.save()

    def write_verbatim(self, upto_turn):
        json.dump([m for t, m in zip(GOV_TURNS, VERBATIM_ALL) if t <= upto_turn], open(self.vfile, "w"), indent=1)

    def abl_env(self):
        return {"DRIFTLEDGER_HOME": self.home, "DRIFTLEDGER_PACKET_MODE": self.mode, "DRIFTLEDGER_GATES": "off",
                "DRIFTLEDGER_REMINDER": "off", "DRIFTLEDGER_VERBATIM_FILE": self.vfile}

    def dl(self, *argv, check=True):
        env = dict(os.environ, **self.abl_env(), PYTHONPATH=ABL)
        p = subprocess.run([sys.executable, "-m", "driftledger", *argv], cwd=self.ws, env=env, capture_output=True, text=True)
        if check and p.returncode: raise SystemExit(f"FAIL {self.id} driftledger {argv[:3]}: {p.stderr[-300:]}")
        return p.stdout

    def render(self, mode=None, reason="compact"):
        env = dict(os.environ, **self.abl_env(), PYTHONPATH=ABL)
        p = subprocess.run([sys.executable, "-m", "driftledger.ablation_render", mode or self.mode, "--reason", reason,
                            "--cwd", self.ws], cwd=self.ws, env=env, capture_output=True, text=True, check=True)
        return p.stdout.rstrip("\n"), p.stderr.strip()

    def ledger(self):
        check_driftledger(); os.environ["DRIFTLEDGER_HOME"] = self.home
        from driftledger import threads; from driftledger.ledger import Ledger
        return Ledger(threads.resolve(self.ws))

    def seed_turn(self, turn):
        """Out-of-band owner seeding for one scenario turn (fixture.SEED recipe, same session tag). fixture.SEED names
        entries L1..L10 assuming an empty store; agent proposals can shift real ids, so nominal ids are remapped to the
        ids the owner seeds actually got (state["seed_ids"])."""
        ids = self.st.setdefault("seed_ids", {})
        nominal = 0
        for gi, (t, argv) in enumerate(fixture.SEED):
            if argv[0] != "consume": nominal += 1
            if t != turn: continue
            key = f"T{turn}:seed:{gi}"
            if key in self.st["log"]: continue
            argv = [ids.get(a, a) if (a.startswith("L") and a[1:].isdigit()) else a for a in argv]
            out = self.dl("--cwd", self.ws, "--session", "seed-oob", "--turn", str(turn), *argv)
            if argv[0] != "consume": ids[f"L{nominal}"] = out.split()[0]
            self.st["log"][key] = {"seed": argv[0], "argv_ids": [a for a in argv[1:] if a.startswith("L")], "out": out.strip()}
            self.save()
        if turn in GOV_TURNS: self.write_verbatim(turn)

    def assert_store(self):
        """Fail-stop only on the 10 owner-seeded entries; agent proposals are recorded as a metric, never fatal."""
        from driftledger import model
        es = self.ledger().state().entries; ids = self.st.get("seed_ids", {})
        want = [(a[0] if a[0] != "except" else "exception") for t, a in fixture.SEED if a[0] != "consume"]
        typ = {"mission": "mission", "forbid": "constraint", "decide": "decision", "park": "parked", "owe": "obligation",
               "boundary": "boundary", "exception": "exception"}
        errs, seeded = [], {}
        for i, v in enumerate(want, 1):
            e = es.get(ids.get(f"L{i}", "?"))
            exp = model.CONSUMED if i == 9 else model.ACTIVE
            ok = e and e.type == typ[v] and e.status == exp and e.proposed_by == model.OWNER
            if not ok: errs.append(f"L{i}->{ids.get(f'L{i}')}: {e and (e.type, e.status, e.proposed_by)} want {(typ[v], exp, 'owner')}")
            if e: seeded[f"L{i}"] = [e.id, e.type, e.status]
        if not (es.get(ids.get("L7", "?")) and es[ids["L7"]].open_obligation): errs.append("L7 not an ACTIVE obligation")
        if errs: raise SystemExit(f"FAIL {self.id} store check before compact1: " + "; ".join(errs))
        own = {v[0] for v in seeded.values()}
        self.st["agent_proposals"] = [{"id": e.id, "type": e.type, "text": e.text, "status": e.status}
                                      for e in es.values() if e.id not in own]
        self.st["log"]["store_check"] = {"ok": True, "entries": seeded, "agent_proposals": len(self.st["agent_proposals"])}
        self.save()

    # ---- injection check ----
    def transcript_files(self):
        d = os.path.join(self.cfg, "projects", runner.slug(os.path.realpath(self.ws)))
        return sorted(glob.glob(os.path.join(d, "*.jsonl")))

    def marker_hits(self, marker):
        def walk(o):
            if isinstance(o, dict):
                if o.get("role") == "assistant" or o.get("type") in ("agent_message", "reasoning"): return
                for v in o.values(): yield from walk(v)
            elif isinstance(o, list):
                for v in o: yield from walk(v)
            elif isinstance(o, str): yield o
        n = 0
        for f in self.transcript_files():
            for line in open(f, errors="replace"):
                try: o = json.loads(line)
                except ValueError: continue
                n += sum(s.count(marker) for s in walk(o))
        return n

    def markers(self):
        return {m: (self.render(m)[0].splitlines() or [""])[0] for m in ARMS.values() if m != "none"}


class AblLineage(AblMixin, runner.Lineage):
    def __init__(self, out, arm, model, seed, scenario):
        super().__init__(out, arm, model, seed, scenario); self.abl_init()

    def command(self, prompt, new_session=False):
        key = "sid2" if new_session else "sid"
        cmd = ["claude", "-p", prompt, "--model", runner.MODELS[self.model], "--dangerously-skip-permissions",
               "--output-format", "json", "--plugin-dir", ABL]
        if self.st.get(key): cmd += ["--resume", self.st[key]]
        return cmd, dict(CLAUDE_CONFIG_DIR=self.cfg, **self.abl_env())

    def claude(self, prompt, new_session=False):
        key = "sid2" if new_session else "sid"
        cmd, extra = self.command(prompt, new_session)
        env = dict(os.environ, **runner.token_env(), **extra)
        p = subprocess.run(cmd, cwd=self.ws, capture_output=True, text=True, timeout=3600, env=env)
        o = p.stdout; b = o.find("{")
        if p.returncode or b < 0: raise SystemExit(f"FAIL {self.id} rc={p.returncode} {p.stderr[-300:]}")
        d = json.loads(o[b:])
        if d.get("is_error"): raise SystemExit(f"FAIL {self.id} {str(d.get('result'))[:300]}")
        self.st[key] = d.get("session_id") or self.st.get(key)
        return d.get("result") or ""

    def snapshot(self, label):
        super().snapshot(label)
        L = self.ledger()
        if L.store.exists():
            import shutil; shutil.copy(L.store.path, os.path.join(self.base, "snapshots", label, "ledger_events.jsonl"))


class AblRunMixin:
    def check_inject(self, L, cid, before):
        mk = L.markers()
        after = {m: L.marker_hits(x) for m, x in mk.items()}
        if L.mode == "none":
            seen = any(after[m] > before[m] for m in mk)
            if seen: raise SystemExit(f"FAIL {L.id} {cid}: none arm shows an injection {after}")
        else:
            seen = after[L.mode] > before[L.mode]
        L.st["inject"][cid] = {"inject_seen": seen, "marker": mk.get(L.mode), "hits_before": before, "hits_after": after}
        L.st["log"][f"{cid}:inject"] = {"inject_seen": seen}; L.save()
        print(f"{L.id} {cid} inject_seen={seen}", flush=True)
        if L.mode != "none" and not seen: raise SystemExit(f"FAIL {L.id} {cid}: no {L.mode} injection seen in transcript")

    def run_lineage(self, L):
        if L.st.get("dry"): raise SystemExit(f"FAIL {L.id}: {L.base} was built by --dry (pre-seeded store); use a fresh --out")
        compacts = 0
        for st in self.sc["steps"]:
            k = st["kind"]
            if k == "owner":
                self.step(L, st["id"], st["text"])                      # careful_owner deliberately NOT called
                if st.get("governing"): L.seed_turn(int(st["id"][1:]))
            elif k == "band": L.snapshot(f"pre_{st['id']}"); self.band(L, st["id"])
            elif k == "compact":
                compacts += 1
                if compacts == 1 and "store_check" not in L.st["log"]: L.assert_store()
                if st["id"] in L.st["log"] and f"{st['id']}:inject" in L.st["log"]: continue
                before = L.st.setdefault("inject_before", {}).get(st["id"])
                if before is None:
                    before = {m: L.marker_hits(x) for m, x in L.markers().items()}
                    L.st["inject_before"][st["id"]] = before; L.save()
                self.step(L, st["id"], "/compact"); L.snapshot(f"after_{st['id']}")
                self.check_inject(L, st["id"], before)
            elif k == "probe":
                if st.get("note") and not os.path.exists(os.path.join(L.ws, st["note"])):
                    open(os.path.join(L.ws, st["note"]), "w").write(st["note_text"])
                self.step(L, st["id"], st["text"], meta={"cell": st.get("cell")})
            elif k == "new_session":
                self.step(L, st["id"], st["text"], new_session=True, meta={"cell": st.get("cell")}); L.snapshot("after_new_session")
            elif k == "codex":
                if st["id"] not in L.st["log"]:
                    L.st["log"][st["id"]] = {"skipped": "X1 second harness skipped in M2 ablation (all arms)"}; L.save()
                    print(f"{L.id} {st['id']} SKIPPED (second harness)", flush=True)

    def dry(self):
        """No model calls: seed a fake walk of the governing steps, print renders + ledger state + would-be commands."""
        for L in self.lineages:
            L.st["dry"] = True; L.save()                              # a dry dir must never be resumed as a real run
            for st in self.sc["steps"]:
                if st["kind"] == "owner" and st.get("governing"): L.seed_turn(int(st["id"][1:]))
            L.assert_store()
            body, tok = L.render()
            print(f"\n===== {L.id}  mode={L.mode}  {tok}\n--- render (compact) ---\n{body or '(nothing injected)'}")
            print(f"--- ledger state ---\n{L.dl('--cwd', L.ws, 'status').strip()}")
            for nid, (eid, t, s) in L.st["log"]["store_check"]["entries"].items(): print(f"  {nid}={eid} {t} {s}")
            print(f"  agent_proposals: {L.st['agent_proposals']}")
            print(f"--- mcp ---\n{self.no_mcp(L)}")
            print("--- would run ---")
            for label, prompt in (("work turn T1", self.sc["steps"][0]["text"]), ("compact1", "/compact")):
                print(f"[{label}] " + self.would_run(L, prompt))
        print("\nDRY DONE (no model calls)")

    def no_mcp(self, L):
        man = json.load(open(os.path.join(ABL, ".claude-plugin", "plugin.json")))
        assert "mcpServers" not in man and not os.path.exists(os.path.join(ABL, ".mcp.json")), "plugin_ablation declares MCP"
        assert not os.path.exists(os.path.join(L.ws, ".mcp.json")), "workspace has .mcp.json"
        cmd, _ = L.command("x")
        assert not any("mcp" in c for c in cmd), "claude argv mentions mcp"
        return "Claude: plugin_ablation manifest has no mcpServers, no .mcp.json (plugin or workspace), no --mcp-config"

    def would_run(self, L, prompt):
        cmd, extra = L.command(prompt)
        return f"cwd={L.ws} env+={{{', '.join(f'{k}={v}' for k, v in extra.items())}}} + token_env() keys\n  " + \
               " ".join(json.dumps(c) if (" " in c or not c) else c for c in cmd)


class AblRun(AblRunMixin, runner.Run):
    def __init__(self, scenario_path, out, specs, kill):
        self.sc = json.load(open(scenario_path)); self.sc["_path"] = os.path.abspath(scenario_path)
        self.out, self.kill = os.path.abspath(out), kill
        self.lineages = [AblLineage(self.out, *s, self.sc) for s in specs]


def parse(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario"); ap.add_argument("--out", required=True); ap.add_argument("--runs", required=True)
    ap.add_argument("--kill", type=float, default=40.0); ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    return a, [(x.split(":")[0], x.split(":")[1], int(x.split(":")[2])) for x in a.runs.split(",")]


def main():
    a, specs = parse(); check_driftledger()
    R = AblRun(a.scenario, a.out, specs, a.kill)
    if a.dry: return R.dry()
    for L in R.lineages: R.run_lineage(L)
    print(f"DONE spend=${R.total_spend():.2f} (Claude, transcript-derived)")


if __name__ == "__main__":
    main()
