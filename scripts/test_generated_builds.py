from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CASES = [("java", False), ("kotlin", True)]

def has_command(command: str) -> bool:
    return shutil.which(command) is not None

def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd, check=True)

def run_copier(destination: Path, language: str, has_service: bool) -> None:
    if not has_command("copier"):
        print("SKIP: copier is not available", file=sys.stderr)
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

def main() -> None:
    for language, has_service in CASES:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"cloche-build-{language}-{has_service}-"))
        try:
            run_copier(temp_dir, language, has_service)
            run([str(temp_dir / "gradlew.bat"), "build", "--no-daemon"], cwd=temp_dir)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
if __name__ == "__main__":
    main()
