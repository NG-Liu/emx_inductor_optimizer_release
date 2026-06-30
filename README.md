# EMX Inductor Target-L Optimizer

This repository packages the validated single-inductor EMX workflow used for the main-path inductor search.
It starts from a target `L@3.75GHz`, proposes high-Q geometries from the local surrogate model, runs Cadence stream-out and EMX on the VM, then selects the best EMX-verified FDL.

The checked-in release intentionally includes representative `runs/**`, `*.gds`, and `*.s2p` results so colleagues can inspect and reproduce the current conclusions without rerunning every sample.

## What Is Included

- 12-sided polygon spiral inductor generator.
- M5/M4/V4 three-metal air-bridge layout flow.
- Cadence SKILL generation, GDS stream-out, and EMX batch execution.
- Differential EMX port convention: `Pdiff=P1:P2`.
- Sweep points: `3.0, 3.5, 4.0, 4.5 GHz`.
- L/Q extraction at `3.75 GHz` by interpolating complex `Zdiff` between `3.5` and `4.0 GHz`.
- Verified example runs under `runs/`, including the `5.367 nH` high-Q refinement.

## VM Access

The VM credentials are intentionally committed in `configs/vm_default.json` for this handoff:

```text
host: 192.168.37.128
user: IC
password: user1111
EMX: /home/IC/EDA/INTEGRAND60/bin/emx
process: /home/IC/EDA/INTEGRAND60/virtuoso_ui/emxinterface/processes/fdl_stack.proc
```

The VM must be running and reachable from Windows before launching EMX.

## Quick Start

Install Python dependencies:

```powershell
cd C:\Users\mechrevo\Desktop\emx_inductor_optimizer_release
python -m pip install -e .
```

Run local validation without touching the VM:

```powershell
python scripts/validate_examples.py
python -m compileall -q src scripts tests
python scripts/select_best.py --root runs/target_L5p367_highQ_refine --target-L 5.367 --tol 0.02
```

Run a VM smoke test on one candidate. Existing valid GDS/S2P files are skipped unless `--force` is added:

```powershell
python scripts/run_emx_persistent.py --manifest runs/target_L5p367_highQ_refine/manifest.csv --limit 1
```

Run the one-command optimization flow for a new target:

```powershell
python scripts/optimize_target_l_emx.py --target-L 5.367 --tol 0.02 --top 12 --out-root runs/target_L5p367_new
```

Generate proposal files only, without VM/EMX:

```powershell
python scripts/optimize_target_l_emx.py --target-L 5.367 --tol 0.02 --top 12 --out-root runs/target_L5p367_proposal --skip-emx
```

## Main Scripts

- `scripts/optimize_target_l_emx.py`: one-command wrapper for proposal, EMX run, best-result selection, and `summary.md`.
- `scripts/propose_target_l.py`: uses the surrogate model to create FDL candidates and `manifest.csv`.
- `scripts/run_emx_persistent.py`: uses one persistent SSH session to run Virtuoso, stream-out, and EMX on the VM.
- `scripts/select_best.py`: reads EMX S2P files and picks max `Q@3.75GHz` within the L tolerance.
- `scripts/validate_examples.py`: small local regression check for the Touchstone parser and L/Q extraction.

## Important Outputs

- `runs/<name>/fdl/*.py`: UltraEM-compatible FDL source for each candidate.
- `runs/<name>/skill/*.il`: generated Cadence SKILL layout builder.
- `runs/<name>/gds/*.gds`: stream-out GDS used by EMX.
- `runs/<name>/s2p/*.s2p`: EMX Touchstone result.
- `runs/<name>/proposal.json`: surrogate-ranked candidate proposal.
- `runs/<name>/best_result.json`: EMX-selected best geometry.
- `runs/<name>/best_fdl/*.py`: copied FDL for the selected best point.
- `runs/<name>/summary.md`: one-command wrapper summary, when generated.

## Current Verified Recommendation

For target `L@3.75GHz = 5.367 nH`, the high-Q refinement run is:

```text
runs/target_L5p367_highQ_refine
```

Using the selection rule "highest EMX Q within +/-0.02 nH":

```text
candidate: LQ_N3p5_R101p45_W10p4_S15
N: 3.5 turns
r0: 101.45 um
W: 10.4 um
S: 15.0 um
L@3.75GHz: 5.372199148 nH
Q@3.75GHz: 42.811131
```

The closest-L point in the same refinement run is:

```text
candidate: LQ_N3p5_R101p35_W10p4_S15
L@3.75GHz: 5.366342047 nH
Q@3.75GHz: 42.779760
```

Use the first point when Q is the priority, and the second point when exact L centering matters more.

## Documentation

- `docs/WORKFLOW.md`: full flow, EMX command convention, and L/Q formulas.
- `docs/EXAMPLES.md`: checked-in reference runs and current best geometry numbers.
- `docs/differential_lq.md`: compact differential L/Q definition.
- `docs/emx_flow.md`: original batch-flow notes.

## Git Notes

This release folder is meant to be submitted as a standalone repository. The copied `.git` directory from the working project was removed, and generated reference artifacts are intentionally not ignored.

