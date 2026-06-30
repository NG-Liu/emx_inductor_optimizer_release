# EMX Target-L Optimization Workflow

This note describes the reproducible flow from target inductance to an EMX-verified FDL file.

## 1. Geometry Proposal

The optimizer searches within geometry bands learned from accepted EMX samples in `data/v1_dataset.csv`.
For each accepted `(N, W, S)` band, it sweeps `r0` and uses `data/v1_model.json` to predict:

```text
L_3p0_nH, Q_3p0
L_3p5_nH, Q_3p5
L_4p0_nH, Q_4p0
L_4p5_nH, Q_4p5
L_3p75_nH, Q_3p75
```

The proposal step keeps diverse candidates by limiting the number per `(N, W, S)` band, then writes:

```text
runs/<target>/fdl/*.py
runs/<target>/manifest.csv
runs/<target>/proposal.json
```

Example:

```powershell
python scripts/propose_target_l.py --target-L 5.367 --tol 0.02 --top 12 --out-root runs/target_L5p367_new
```

## 2. FDL to Cadence Layout

Each generated FDL is converted to a Cadence SKILL layout builder.
The SKILL script creates a layout cell in the VM Cadence library:

```text
library: codex_fdl_bridge
view: layout
tech lib: smic13mmrf_1233
```

The generated layout uses:

```text
spiral metal: m5
underpass/bridge metal: m4
vias: v4
pins: P1 and P2 on m5
```

## 3. Stream-Out and EMX

`scripts/run_emx_persistent.py` opens one persistent SSH session to the VM, uploads FDL/SKILL files, runs Virtuoso in batch mode, streams out GDS, then runs EMX.

The core EMX command options are:

```text
--3d=m4,m5
--via-sidewalls=v4
--via-inductance=v4
--sweep 3e9 4.5e9
--sweep-stepsize=5e8
--format=touchstone
--s-impedance=50
--internal=P1,m5,8
--internal=P2,m5,8
-p Pdiff=P1:P2
```

This produces a differential one-port Touchstone file for each candidate:

```text
runs/<target>/s2p/*.s2p
```

It also downloads the exact GDS used by EMX:

```text
runs/<target>/gds/*.gds
```

## 4. L/Q Extraction

The target frequency is `3.75 GHz`. EMX is swept only at:

```text
3.0, 3.5, 4.0, 4.5 GHz
```

For the main `3.75 GHz` value, do not interpolate L or Q directly.
First interpolate complex differential impedance:

```text
Zdiff(3.75GHz) = 0.5 * Zdiff(3.5GHz) + 0.5 * Zdiff(4.0GHz)
```

For EMX differential one-port output:

```text
Zdiff = Z0 * (1 + S11) / (1 - S11)
```

For generic two-port Touchstone comparison files:

```text
Zdiff = Z11 + Z22 - Z12 - Z21
```

Then calculate:

```text
L = imag(Zdiff) / (2 * pi * f)
Q = abs(imag(Zdiff) / real(Zdiff))
```

The code that implements this is `src/inductor_lq/touchstone.py`.

## 5. Best-Point Selection

`scripts/select_best.py` evaluates all valid S2P files in a run directory.
The selection rule is:

```text
1. Keep EMX results with |L_3p75_nH - target_L| <= tolerance.
2. Select the highest Q_3p75 inside that feasible pool.
3. If no result is inside tolerance, select the closest-L result.
```

The result is written to:

```text
runs/<target>/best_result.json
runs/<target>/best_fdl/*.py
```

## 6. One-Command Flow

The recommended colleague-facing entry point is:

```powershell
python scripts/optimize_target_l_emx.py --target-L 5.367 --tol 0.02 --top 12 --out-root runs/target_L5p367_new
```

This runs:

```text
propose_target_l.py
run_emx_persistent.py
select_best.py
```

and writes:

```text
runs/<target>/summary.md
```

Use `--skip-emx` for proposal-only review, or `--force` to rerun EMX even if valid GDS/S2P files already exist.

