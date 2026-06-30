# Checked-In Example Results

This release includes reference runs so colleagues can compare geometry, GDS, S2P, and extracted L/Q without rerunning all EMX jobs.

## Target 5.367 nH: High-Q Refinement

Run directory:

```text
runs/target_L5p367_highQ_refine
```

Selection rule:

```text
highest EMX Q@3.75GHz within +/-0.02 nH of target L
```

Selected best-Q point:

```text
candidate: LQ_N3p5_R101p45_W10p4_S15
N: 3.5 turns
r0: 101.45 um
W: 10.4 um
S: 15.0 um
outer radius: 190.35 um
L@3.75GHz: 5.372199148 nH
L error: +0.005199148 nH
Q@3.75GHz: 42.811131
best FDL: runs/target_L5p367_highQ_refine/best_fdl/LQ_N3p5_R101p45_W10p4_S15.py
```

Closest-L point in the same run:

```text
candidate: LQ_N3p5_R101p35_W10p4_S15
N: 3.5 turns
r0: 101.35 um
W: 10.4 um
S: 15.0 um
outer radius: 190.25 um
L@3.75GHz: 5.366342047 nH
L error: -0.000657953 nH
Q@3.75GHz: 42.779760
```

Use `R101p45` when maximum Q is the priority. Use `R101p35` when centering the L value is more important than the small Q gain.

Reproduce the selection:

```powershell
python scripts/select_best.py --root runs/target_L5p367_highQ_refine --target-L 5.367 --tol 0.02
```

## Target 5.367 nH: Smaller-Area Fallback

Run directory:

```text
runs/target_L5p367_highQ
```

Representative smaller-area candidate:

```text
candidate: LQ_N4p5_R56p4_W12_S16
N: 4.5 turns
r0: 56.4 um
W: 12.0 um
S: 16.0 um
outer radius: 182.4 um
L@3.75GHz: 5.370727748 nH
Q@3.75GHz: 39.479502
```

This option trades Q for a smaller outer radius compared with the high-Q `N=3.5` refinement.

## Target 4.51 nH: Quick Run

Run directory:

```text
runs/target_L4p51_quick
```

Selected best-Q point inside `+/-0.02 nH`:

```text
candidate: LQ_N4p5_R48p05_W10p4_S14
N: 4.5 turns
r0: 48.05 um
W: 10.4 um
S: 14.0 um
outer radius: 157.85 um
L@3.75GHz: 4.519416677 nH
L error: +0.009416677 nH
Q@3.75GHz: 35.965302
best FDL: runs/target_L4p51_quick/best_fdl/LQ_N4p5_R48p05_W10p4_S14.py
```

Closest-L point in the same run:

```text
candidate: LQ_N4p5_R47p9_W10p4_S14
L@3.75GHz: 4.511917741 nH
Q@3.75GHz: 35.703780
```

Reproduce the selection:

```powershell
python scripts/select_best.py --root runs/target_L4p51_quick --target-L 4.51 --tol 0.02
```

## Useful Interpretation

For this flow, "best" means "highest Q among candidates that meet the L tolerance", not necessarily the numerically closest L.
If a schematic requires tighter centering, sort the `ranked_results` array in `best_result.json` by absolute `L_error_nH` instead.

