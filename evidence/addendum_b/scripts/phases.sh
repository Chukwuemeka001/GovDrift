#!/bin/zsh
# Arm-F run: phase A = fork..R1P4 ; B = reply R1P4..R2P4 ; C = reply R2P4..final archive
set -e
cd "$(dirname $0)"
P=$1; PH=$2; D() { python3 drive_lineages.py "$@"; }
export GOVDRIFT_CONCURRENCY=${GOVDRIFT_CONCURRENCY:-2}
case $PH in
  A) D fork --project $P
     for pr in R1P1 R1P2 R1P3 R1P4; do D probe --project $P --round 1 --probe $pr; done ;;
  B) D reply --project $P --round 1 --probe R1P4 --decisions decisions_${P}_R1P4.json
     D probe --project $P --round 1 --probe R1P5
     D turn  --project $P --round 1 --step WB1
     D probe --project $P --round 1 --probe R1P6
     D turn  --project $P --round 1 --step W2
     D turn  --project $P --round 1 --step W3
     D workto-band --project $P --round 1
     D compact --project $P --round 1
     D archive --project $P --label postcompact2
     for pr in R2P1 R2P2 R2P3 R2P4; do D probe --project $P --round 2 --probe $pr; done ;;
  C) D reply --project $P --round 2 --probe R2P4 --decisions decisions_${P}_R2P4.json
     D probe --project $P --round 2 --probe R2P5
     D probe --project $P --round 2 --probe R2P6
     D archive --project $P --label final ;;
  D) D fork-orig --project $P
     D workto-band --project $P --round 2
     python3 -c "
import json,sys;p='state_$P'+'_lineages.json';d=json.load(open(p))
for l in d['lineages'].values(): l.setdefault('precompact3_context', l.get('last_context'))
json.dump(d,open(p,'w'),indent=2)"
     D compact --project $P --round 2
     D snapshot --project $P --round 3
     D archive --project $P --label postcompact3
     python3 build_gen3_payloads.py $P
     for pr in R3P1 R3P2 R3P3 R3P4 R3P5; do D probe --project $P --round 3 --probe $pr --payload-dir payloads/$P/gen3; done
     python3 place_note.py $P
     D probe --project $P --round 3 --probe R3P6 --payload-dir payloads/$P/gen3
     D archive --project $P --label final3 ;;
esac
echo "PHASE $PH $P DONE"
