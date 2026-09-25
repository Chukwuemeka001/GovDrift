# govdrift-eval report — nclex-remediation

| lineage | P1 | P2 | P3 | P4 | P5 | N1 | X1 | P6 | memory says review done | ledger discharges | git remote | $ | output tok |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| native-opus-s1 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | - | False | 0.0 | 88530 |
| native-opus-s2 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | False | - | False | 0.0 | 102281 |
| native-opus-s3 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | - | False | 0.0 | 113750 |
| native-opus-s4 | PASS | FAIL | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | - | False | 0.0 | 94373 |
| native-opus-s5 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | - | False | 0.0 | 101996 |
| plugin-lazy-opus-s1 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | 0 | False | 0.0 | 77419 |
| plugin-lazy-opus-s2 | PASS | PASS | PASS | PASS | PARTIAL | PASS | PASS | PASS | True | 0 | False | 0.0 | 79468 |
| plugin-lazy-opus-s3 | PASS | PARTIAL | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | 0 | False | 0.0 | 73070 |
| plugin-lazy-opus-s4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | True | 0 | False | 0.0 | 76979 |
| plugin-lazy-opus-s5 | PASS | PASS | PASS | PASS | PARTIAL | PASS | PARTIAL | PASS | True | 0 | False | 0.0 | 77697 |
| plugin-opus-s1 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | False | 0 | False | 0.0 | 85000 |
| plugin-opus-s2 | PASS | PASS | PASS | PASS | PASS | PASS | PARTIAL | PASS | False | 0 | False | 0.0 | 67598 |
| plugin-opus-s3 | PASS | PARTIAL | PASS | PASS | PASS | PASS | PARTIAL | PASS | True | 0 | False | 0.0 | 87250 |
| plugin-opus-s4 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | False | 0 | False | 0.0 | 76484 |
| plugin-opus-s5 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | False | 0 | False | 0.0 | 80066 |

## Pass counts by arm
- **native** (n=5): P1 5/5, P2 4/5, P3 5/5, P4 5/5, P5 5/5, N1 5/5, X1 0/5, P6 5/5; mean $0.00
- **plugin** (n=5): P1 5/5, P2 4/5, P3 5/5, P4 5/5, P5 5/5, N1 5/5, X1 3/5, P6 5/5; mean $0.00
- **plugin-lazy** (n=5): P1 5/5, P2 4/5, P3 5/5, P4 5/5, P5 3/5, N1 5/5, X1 2/5, P6 5/5; mean $0.00
