# GitHub Submission Notes

This folder is a standalone release repository for the EMX target-L inductor optimizer.

## Recommended Commit Scope

Include all files in this directory:

```text
configs/
data/
docs/
runs/
scripts/
src/
tests/
.gitattributes
.gitignore
README.md
SUBMISSION.md
pyproject.toml
```

The `runs/` directory is intentionally included. It contains reference FDL, SKILL, GDS, S2P, proposal, and best-result files so reviewers can inspect the complete EMX evidence chain.

## Credentials

`configs/vm_default.json` intentionally contains the VM password for this internal handoff:

```text
user: IC
password: user1111
host: 192.168.37.128
```

Do not publish this repository publicly unless the credentials are removed or rotated.

## Local Validation

Before pushing:

```powershell
python -m pip install -e .
python scripts/validate_examples.py
python -m compileall -q src scripts tests
python scripts/select_best.py --root runs/target_L5p367_highQ_refine --target-L 5.367 --tol 0.02
```

## One-Command Optimization Example

```powershell
python scripts/optimize_target_l_emx.py --target-L 5.367 --tol 0.02 --top 12 --out-root runs/target_L5p367_new
```

Use `--skip-emx` to generate FDL/manifest/proposal only. Use `--force` to rerun EMX even when valid S2P/GDS files already exist.

## Push To GitHub

After creating the GitHub repository, add the remote and push:

```powershell
git remote add origin <github-repo-url>
git push -u origin main
```

