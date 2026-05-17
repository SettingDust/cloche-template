from __future__ import annotations
import os
from pathlib import Path
from testlib import generated_project, run
CASES = [("java", False), ("kotlin", True)]

def gradle_command(root: Path) -> list[str]:
    if os.name == "nt":
        return [str(root / "gradlew.bat"), "build", "--no-daemon"]
    return [str(root / "gradlew"), "build", "--no-daemon"]

def main() -> None:
    if os.environ.get("CLOCHE_RUN_SLOW_TESTS") != "1":
        print("SKIP: set CLOCHE_RUN_SLOW_TESTS=1 to run generated Gradle builds", flush=True)
        return
    for language, has_service in CASES:
        print(f"== build language={language} has_service={has_service}", flush=True)
        with generated_project(language, has_service, prefix="cloche-build") as root:
            run(gradle_command(root), cwd=root)
if __name__ == "__main__":
    main()
