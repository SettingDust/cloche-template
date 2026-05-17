from __future__ import annotations
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
ROOT = Path(__file__).resolve().parents[1]

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def has_command(command: str) -> bool:
    return shutil.which(command) is not None

def run(command: list[str], cwd: Path | None = None) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)

def run_copier(destination: Path, language: str, has_service: bool) -> None:
    if not has_command("copier"):
        print("SKIP: copier is not available", file=sys.stderr, flush=True)
        raise SystemExit(0)
    run([
        "copier",
        "copy",
        str(ROOT),
        str(destination),
        "--trust",
        "--vcs-ref=HEAD",
        "--defaults",
        "--data",
        "name=TestMod",
        "--data",
        f"language={language}",
        "--data",
        f"has_service={'true' if has_service else 'false'}",
    ])
@contextmanager
def generated_project(language: str, has_service: bool, prefix: str = "cloche-template") -> Iterator[Path]:
    temp_dir = Path(tempfile.mkdtemp(prefix=f"{prefix}-{language}-{has_service}-"))
    try:
        print(f"== generate language={language} has_service={has_service} into {temp_dir}", flush=True)
        run_copier(temp_dir, language, has_service)
        yield temp_dir
    finally:
        if os.environ.get("CLOCHE_KEEP_TEST_PROJECTS"):
            print(f"KEEP: {temp_dir}", flush=True)
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)
