from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inductor_lq.candidates import format_size_token


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_step(name: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    printable = " ".join(command)
    print(f"\n== {name} ==")
    print(printable)
    proc = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.returncode:
        raise RuntimeError(f"{name} failed with exit code {proc.returncode}")
    return proc


def read_best(best_path: Path) -> dict[str, object] | None:
    if not best_path.exists():
        return None
    return json.loads(best_path.read_text(encoding="utf-8"))


def write_summary(
    summary_path: Path,
    *,
    target_l: float,
    tolerance: float,
    top: int,
    out_root: Path,
    vm_config: Path,
    proposal_only: bool,
    commands: list[list[str]],
    best_result: dict[str, object] | None,
) -> None:
    lines = [
        f"# Target-L EMX Optimization Summary",
        "",
        f"- Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Target L@3.75GHz: `{target_l:.6f} nH`",
        f"- Tolerance: `+/-{tolerance:.6f} nH`",
        f"- Candidate count requested: `{top}`",
        f"- Run root: `{rel(out_root)}`",
        f"- VM config: `{rel(vm_config)}`",
        f"- Proposal only: `{proposal_only}`",
        "",
    ]

    if best_result:
        best = best_result["best"]
        lines.extend(
            [
                "## Best EMX Result",
                "",
                f"- Candidate: `{best['candidate_id']}`",
                f"- Geometry: `N={best['N_turns']}`, `r0={best['r0_um']} um`, `W={best['W_um']} um`, `S={best['S_um']} um`",
                f"- L@3.75GHz: `{best['L_3p75_nH']:.9f} nH`",
                f"- L error: `{best['L_error_nH']:+.9f} nH`",
                f"- Q@3.75GHz: `{best['Q_3p75']:.6f}`",
                f"- Best FDL copy: `{best_result['best_fdl']}`",
                f"- Best-result JSON: `{rel(out_root / 'best_result.json')}`",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Best EMX Result",
                "",
                "No EMX selection was run. Use the same command without `--skip-emx` after the VM is reachable.",
                "",
            ]
        )

    lines.extend(["## Commands", ""])
    for command in commands:
        lines.extend(["```powershell", " ".join(command), "```", ""])

    summary_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="One-command target-L inductor optimization: propose candidates, run EMX, select best Q."
    )
    parser.add_argument("--target-L", type=float, required=True, help="Target L@3.75GHz in nH.")
    parser.add_argument("--tol", type=float, default=0.05, help="Allowed EMX L error in nH.")
    parser.add_argument("--top", type=int, default=20, help="Number of candidates to propose.")
    parser.add_argument("--out-root", type=Path, default=None, help="Run directory. Default: runs/target_L<target>.")
    parser.add_argument("--limit", type=int, default=None, help="Only run the first N manifest rows through EMX.")
    parser.add_argument("--force", action="store_true", help="Re-run EMX even when valid GDS/S2P files already exist.")
    parser.add_argument("--vm-config", type=Path, default=ROOT / "configs" / "vm_default.json")
    parser.add_argument("--model", type=Path, default=ROOT / "data" / "v1_model.json")
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "v1_dataset.csv")
    parser.add_argument("--r0-step", type=float, default=0.25)
    parser.add_argument("--per-band-limit", type=int, default=4)
    parser.add_argument("--max-error", type=float, default=0.25, help="Maximum predicted L error in nH.")
    parser.add_argument("--l-model", default=None, help="Optional model key for L prediction.")
    parser.add_argument("--q-model", default="linear", help="Model key for Q ranking.")
    parser.add_argument("--skip-emx", action="store_true", help="Generate proposal/manifest only; do not run EMX or select.")
    args = parser.parse_args()

    out_root = args.out_root or ROOT / "runs" / f"target_L{format_size_token(args.target_L)}"
    out_root = out_root if out_root.is_absolute() else ROOT / out_root
    vm_config = args.vm_config if args.vm_config.is_absolute() else ROOT / args.vm_config
    model = args.model if args.model.is_absolute() else ROOT / args.model
    dataset = args.dataset if args.dataset.is_absolute() else ROOT / args.dataset

    commands: list[list[str]] = []

    propose_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "propose_target_l.py"),
        "--target-L",
        str(args.target_L),
        "--tol",
        str(args.tol),
        "--top",
        str(args.top),
        "--out-root",
        str(out_root),
        "--model",
        str(model),
        "--dataset",
        str(dataset),
        "--r0-step",
        str(args.r0_step),
        "--per-band-limit",
        str(args.per_band_limit),
        "--max-error",
        str(args.max_error),
        "--q-model",
        args.q_model,
    ]
    if args.l_model:
        propose_cmd.extend(["--l-model", args.l_model])
    commands.append(propose_cmd)
    run_step("propose candidates", propose_cmd)

    if not args.skip_emx:
        manifest = out_root / "manifest.csv"
        emx_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "run_emx_persistent.py"),
            "--manifest",
            str(manifest),
            "--vm-config",
            str(vm_config),
        ]
        if args.limit is not None:
            emx_cmd.extend(["--limit", str(args.limit)])
        if args.force:
            emx_cmd.append("--force")
        commands.append(emx_cmd)
        run_step("run EMX", emx_cmd)

        select_cmd = [
            sys.executable,
            str(ROOT / "scripts" / "select_best.py"),
            "--root",
            str(out_root),
            "--target-L",
            str(args.target_L),
            "--tol",
            str(args.tol),
        ]
        commands.append(select_cmd)
        run_step("select best", select_cmd)

    best_result = None if args.skip_emx else read_best(out_root / "best_result.json")
    summary_path = out_root / "summary.md"
    write_summary(
        summary_path,
        target_l=args.target_L,
        tolerance=args.tol,
        top=args.top,
        out_root=out_root,
        vm_config=vm_config,
        proposal_only=args.skip_emx,
        commands=commands,
        best_result=best_result,
    )
    print(f"\nsummary={summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
