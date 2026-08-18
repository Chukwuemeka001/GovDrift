#!/bin/zsh
# Tier 1 runner — parameterized from tier3/runner.sh + the H9-verified fork procedure.
# Drives real headless Claude Code sessions for the GovDrift experiment.
#
# Layout convention (created on demand):
#   $ROOT/projects/<proj>/worker/            worker workspace (one per project)
#   $ROOT/projects/<proj>/arms/<arm>-s<seed>/  per-arm-per-seed workspace copies
#   $ROOT/transcripts/                        archived session JSONLs (the archive of record)
#
# Commands:
#   ./runner1.sh new     <workspace> "<prompt>"          start session in workspace
#   ./runner1.sh turn    <workspace> <sid> "<prompt>"    resume session with prompt
#   ./runner1.sh compact <workspace> <sid>               trigger /compact (headless never auto-compacts — H9)
#   ./runner1.sh usage   <workspace> <sid>               context estimate from session JSONL
#   ./runner1.sh archive <workspace> <sid> <label>       copy session JSONL to $ROOT/transcripts + hash
#   ./runner1.sh clonews <src_ws> <dst_ws>               cp -R workspace + hash-diff manifests (must match)
#   ./runner1.sh fork    <src_ws> <sid> <dst_ws>         copy session JSONL w/ session-id + cwd rewrite
#                                                        into dst_ws's project slug; prints NEW_SESSION
#
# Env overrides: GOVDRIFT_ROOT, GOVDRIFT_MODEL.
# All sessions: --dangerously-skip-permissions is acceptable ONLY because workspaces are
# disposable dirs inside $ROOT. Never point a workspace at anything outside $ROOT.

set -euo pipefail
ROOT="${GOVDRIFT_ROOT:-/Users/emeka/agent-continuity-handoff-20260817/tier1-prep/run}"
MODEL="${GOVDRIFT_MODEL:-claude-haiku-4-5-20251001}"

slug() { printf '%s' "$1" | tr '/' '-' ; }   # /Users/x/y -> -Users-x-y (Claude project slug)
projdir() { echo "$HOME/.claude/projects/$(slug "$1")" ; }

show_result() {
  python3 -c "import json,sys; s=sys.stdin.read(); s=s[s.find('{'):]; d=json.loads(s); \
print('SESSION:', d.get('session_id')); print('COST:', d.get('total_cost_usd')); \
u=d.get('usage',{}); print('IN:', u.get('input_tokens'), 'CACHE_READ:', u.get('cache_read_input_tokens'), 'CACHE_CREATE:', u.get('cache_creation_input_tokens'), 'OUT:', u.get('output_tokens')); \
print(d.get('result','')[:2000])"
  # NOTE: s[s.find('{'):] — JSON output sometimes has a stdin-warning line prepended (H9).
}

cmd="$1"; shift
case "$cmd" in
  new)
    ws="$1"; prompt="$2"; mkdir -p "$ws"; cd "$ws"
    claude -p "$prompt" --model "$MODEL" --dangerously-skip-permissions --output-format json \
      | tee "$ROOT/last_result.json" | show_result
    ;;
  turn)
    ws="$1"; sid="$2"; prompt="$3"; cd "$ws"
    claude -p "$prompt" --resume "$sid" --model "$MODEL" --dangerously-skip-permissions --output-format json \
      | tee "$ROOT/last_result.json" | show_result
    ;;
  compact)
    ws="$1"; sid="$2"; cd "$ws"
    claude -p "/compact" --resume "$sid" --model "$MODEL" --dangerously-skip-permissions --output-format json \
      | tee "$ROOT/last_result.json" | show_result
    ;;
  usage)
    ws="$1"; sid="$2"; f="$(projdir "$ws")/$sid.jsonl"
    python3 - "$f" <<'EOF'
import json, sys
total = 0; last_usage = None
with open(sys.argv[1]) as fh:
    for line in fh:
        try: rec = json.loads(line)
        except Exception: continue
        m = rec.get("message") or {}
        u = m.get("usage")
        if u: last_usage = u
        c = m.get("content")
        if isinstance(c, str): total += len(c)
        elif isinstance(c, list):
            for x in c:
                if isinstance(x, dict): total += len(json.dumps(x))
print("approx content tokens:", total // 4)
if last_usage:
    # per-turn context = cache_read + input + cache_creation (H9)
    ctx = (last_usage.get("cache_read_input_tokens") or 0) + \
          (last_usage.get("input_tokens") or 0) + \
          (last_usage.get("cache_creation_input_tokens") or 0)
    print("last-turn context estimate:", ctx)
    print("last turn usage:", json.dumps(last_usage))
EOF
    ;;
  archive)
    ws="$1"; sid="$2"; label="$3"; mkdir -p "$ROOT/transcripts"
    cp "$(projdir "$ws")/$sid.jsonl" "$ROOT/transcripts/${label}_${sid}.jsonl"
    shasum -a 256 "$ROOT/transcripts/${label}_${sid}.jsonl"
    ;;
  clonews)
    src="$1"; dst="$2"
    [ -e "$dst" ] && { echo "ERROR: $dst exists"; exit 1; }
    find "$src" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
    ( cd "$src" && find . -type f | sort | xargs shasum -a 256 ) > /tmp/govdrift_src_manifest.$$
    cp -R "$src" "$dst"
    ( cd "$dst" && find . -type f | sort | xargs shasum -a 256 ) > /tmp/govdrift_dst_manifest.$$
    if diff -q /tmp/govdrift_src_manifest.$$ /tmp/govdrift_dst_manifest.$$ >/dev/null; then
      echo "CLONE-OK: manifests identical ($(wc -l < /tmp/govdrift_src_manifest.$$) files)"
      cp /tmp/govdrift_src_manifest.$$ "$dst/FORK_MANIFEST.sha256"
    else
      echo "CLONE-MISMATCH — aborting"; diff /tmp/govdrift_src_manifest.$$ /tmp/govdrift_dst_manifest.$$; exit 1
    fi
    rm -f /tmp/govdrift_src_manifest.$$ /tmp/govdrift_dst_manifest.$$
    ;;
  fork)
    src_ws="$1"; sid="$2"; dst_ws="$3"
    src_f="$(projdir "$src_ws")/$sid.jsonl"
    [ -f "$src_f" ] || { echo "ERROR: $src_f not found"; exit 1; }
    new_sid="$(uuidgen | tr 'A-Z' 'a-z')"
    dst_dir="$(projdir "$dst_ws")"; mkdir -p "$dst_dir"
    python3 - "$src_f" "$dst_dir/$new_sid.jsonl" "$sid" "$new_sid" "$src_ws" "$dst_ws" <<'EOF'
import sys
src, dst, old_sid, new_sid, old_cwd, new_cwd = sys.argv[1:7]
with open(src) as f: data = f.read()
data = data.replace(old_sid, new_sid).replace(old_cwd, new_cwd)
with open(dst, "w") as f: f.write(data)
print("rewrote", src, "->", dst)
EOF
    shasum -a 256 "$src_f" "$dst_dir/$new_sid.jsonl"
    echo "NEW_SESSION: $new_sid"
    echo "VERIFY next: ./runner1.sh turn '$dst_ws' $new_sid '<probe>' must resume cleanly."
    ;;
  *) echo "unknown cmd: $cmd"; exit 1;;
esac
