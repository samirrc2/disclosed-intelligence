"""
replication_check.py — run analyze.py twice into two temp folders and assert the
tables are byte-identical, proving determinism. Writes results/latest/replication_check.md.
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import io_paths

HERE = Path(__file__).resolve().parent


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_once(tag):
    out = io_paths.results_root() / f"_repl_{tag}"
    if out.exists():
        shutil.rmtree(out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, P10_OUT_DIR=str(out))
    subprocess.run([sys.executable, str(HERE / "analyze.py")], check=True, env=env,
                   cwd=str(HERE))
    return out


def main():
    a = run_once("a")
    b = run_once("b")
    files = sorted(p.name for p in (a / "tables").glob("*"))
    lines = ["# Replication check\n", f"Compared {len(files)} table artifacts from two independent runs.\n",
             "| table | sha256 (run A) | identical in run B |", "|---|---|---|"]
    ok = True
    for f in files:
        ha = sha(a / "tables" / f)
        hb = sha(b / "tables" / f)
        same = ha == hb
        ok = ok and same
        lines.append(f"| {f} | `{ha[:16]}…` | {'yes' if same else 'NO'} |")
    verdict = "PASS — all table artifacts byte-identical across runs." if ok else "FAIL — non-determinism detected."
    lines.insert(1, f"**{verdict}**\n")
    dest = io_paths.results_root() / "latest"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "replication_check.md").write_text("\n".join(lines) + "\n")
    shutil.rmtree(a)
    shutil.rmtree(b)
    print(verdict)
    print(f"[replication_check] wrote {dest/'replication_check.md'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
