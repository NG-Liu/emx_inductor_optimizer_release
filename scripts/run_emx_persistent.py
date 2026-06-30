from __future__ import annotations

import csv
import json
import posixpath
import sys
import time
from dataclasses import replace
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from inductor_lq.config import VmConfig
from inductor_lq.emx import prepare_skill, sh_quote, streamout_and_emx_command
from inductor_lq.touchstone import read_touchstone


def load_vm_config(path: Path) -> tuple[VmConfig, str | None]:
    if not path.exists():
        return VmConfig(), None
    data = json.loads(path.read_text(encoding="utf-8"))
    password = data.pop("password", None)
    return replace(VmConfig(), **data), password


def is_valid_s2p(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = read_touchstone(path)
    except Exception:
        return False
    return len(data.freqs_hz) == 4 and all(
        abs(actual - expected) < 1.0
        for actual, expected in zip(data.freqs_hz, (3.0e9, 3.5e9, 4.0e9, 4.5e9))
    )


class PersistentRemote:
    def __init__(self, cfg: VmConfig, password: str):
        self.cfg = cfg
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=cfg.host,
            username=cfg.user,
            password=password,
            timeout=90,
            banner_timeout=90,
            auth_timeout=90,
            look_for_keys=False,
            allow_agent=False,
        )
        self.sftp = self.client.open_sftp()

    def close(self) -> None:
        self.sftp.close()
        self.client.close()

    def run(self, command: str) -> None:
        _, stdout, stderr = self.client.exec_command(command)
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                print(stdout.channel.recv(65536).decode("utf-8", "ignore"), end="")
            if stdout.channel.recv_stderr_ready():
                print(stdout.channel.recv_stderr(65536).decode("utf-8", "ignore"), end="", file=sys.stderr)
            time.sleep(0.5)
        while stdout.channel.recv_ready():
            print(stdout.channel.recv(65536).decode("utf-8", "ignore"), end="")
        while stdout.channel.recv_stderr_ready():
            print(stdout.channel.recv_stderr(65536).decode("utf-8", "ignore"), end="", file=sys.stderr)
        status = stdout.channel.recv_exit_status()
        if status:
            raise RuntimeError(f"Remote command failed ({status}): {command}")

    def upload(self, local: Path, remote: str) -> None:
        self.sftp.put(str(local), remote)

    def download(self, remote: str, local: Path) -> None:
        local.parent.mkdir(parents=True, exist_ok=True)
        self.sftp.get(remote, str(local))


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run Cadence streamout + EMX using one persistent SSH session.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--vm-config", type=Path, default=ROOT / "configs" / "vm_default.json")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    cfg, password = load_vm_config(args.vm_config)
    if not password:
        raise RuntimeError(f"No password found in {args.vm_config}")

    run_root = args.manifest.parent
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if args.limit:
        rows = rows[: args.limit]

    for row in rows:
        prepare_skill(run_root / row["fdl_path"], run_root / row["skill_path"], row["candidate_id"], cfg)

    remote = PersistentRemote(cfg, password)
    try:
        for index, row in enumerate(rows, start=1):
            cid = row["candidate_id"]
            local_s2p = run_root / row["s2p_path"]
            local_gds = run_root / row["gds_path"]
            if not args.force and local_gds.exists() and is_valid_s2p(local_s2p):
                print(f"[{index}/{len(rows)}] {cid} skip existing")
                continue

            remote_fdl = posixpath.join(cfg.remote_root, "fdl", f"{cid}.py")
            remote_skill = posixpath.join(cfg.remote_root, "skill", f"{cid}.il")
            remote_run = posixpath.join(cfg.remote_root, "emx", cid)
            print(f"[{index}/{len(rows)}] {cid} upload")
            remote.run(
                "mkdir -p "
                + " ".join(
                    sh_quote(path)
                    for path in (posixpath.dirname(remote_fdl), posixpath.dirname(remote_skill), remote_run)
                )
            )
            remote.upload(run_root / row["fdl_path"], remote_fdl)
            remote.upload(run_root / row["skill_path"], remote_skill)

            print(f"[{index}/{len(rows)}] {cid} virtuoso/strmout/emx")
            remote.run("bash -lc " + sh_quote(streamout_and_emx_command(cfg, cid, remote_run)))
            remote.download(posixpath.join(remote_run, f"{cid}.s2p"), local_s2p)
            remote.download(posixpath.join(remote_run, f"{cid}.gds"), local_gds)
            print(f"[{index}/{len(rows)}] {cid} done -> {local_s2p}")
    finally:
        remote.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
