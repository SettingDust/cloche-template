from __future__ import annotations
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def has_command(command: str) -> bool:
    return shutil.which(command) is not None

def run_copier(destination: Path, language: str, has_service: bool) -> None:
    if not has_command("copier"):
        print("SKIP: copier is not available", file=sys.stderr)
        raise SystemExit(0)
    command = [
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
    ]
    subprocess.run(command, check=True)

def generated(language: str, has_service: bool):
    temp_dir = Path(tempfile.mkdtemp(prefix=f"cloche-template-{language}-{has_service}-"))
    try:
        run_copier(temp_dir, language, has_service)
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def dirs_named(root: Path, name: str) -> list[Path]:
    return [path for path in (root / "src").rglob(name) if path.is_dir()]

def assert_language_cleanup(root: Path, language: str, has_service: bool) -> None:
    if language == "java":
        require(not dirs_named(root, "kotlin"), "language=java must remove all src/**/main/kotlin directories.")
    if language == "kotlin" and not has_service:
        require(not dirs_named(root, "java"), "language=kotlin has_service=false must remove all src/**/main/java directories.")
    bootstrap_kotlin = [path for path in dirs_named(root, "kotlin") if "bootstrap" in path.parts]
    require(not bootstrap_kotlin, "Bootstrap targets must not contain kotlin source directories.")

def assert_service_split(root: Path, has_service: bool) -> None:
    if not has_service:
        for relative in ("src/forge/bootstrap", "src/neoforge/bootstrap", "src/minecraft"):
            require(not (root / relative).exists(), f"has_service=false must remove {relative}.")
        return
    for version in ("20.1", "21.1", "26.1"):
        common_services = root / "src" / "common" / version / "main" / "resources" / "META-INF" / "services"
        minecraft_services = root / "src" / "minecraft" / version / "main" / "resources" / "META-INF" / "services"
        for service in ("IdentifierFactory", "MinecraftAdapter"):
            name = f"settingdust.test_mod.util.{service}"
            require(not (common_services / name).exists(), f"has_service=true must move {name} out of common {version} sources.")
            require((minecraft_services / name).is_file(), f"has_service=true must create minecraft {version} service {name}.")

def assert_entrypoints_and_metadata(root: Path, language: str) -> None:
    build = (root / "build.gradle.kts").read_text(encoding="utf-8")
    base_plugin = (root / "buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts").read_text(encoding="utf-8")
    metadata = (root / "buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt").read_text(encoding="utf-8")
    kotlin_plugin = (root / "buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts").read_text(encoding="utf-8")
    java_plugin = (root / "buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts").read_text(encoding="utf-8")
    require('id("clocheTemplate.base")' in build, "Generated build must apply base convention plugin.")
    require("clocheTemplateMetadata(project)" in base_plugin, "Generated base plugin must apply shared metadata convention.")
    require("modId.set(id)" in metadata, "Generated metadata convention must configure mod id.")
    require("sources.set(source)" in metadata, "Generated metadata convention must configure source metadata.")
    if language == "kotlin":
        require('adapter.set("kotlin")' in kotlin_plugin, "Kotlin generated build must use Kotlin Fabric entrypoint adapter.")
        require('modLoader.set("klf")' in kotlin_plugin, "Kotlin generated build must use KLF Forge-like loader.")
    else:
        require('entrypoint("main", "${project.group}.fabric.${modName}Fabric")' in java_plugin, "Java generated build must configure Fabric main entrypoint.")
        require('modLoader.set("javafml")' in java_plugin, "Java generated build must use javafml Forge-like loader.")

def assert_no_service_false_minecraft_reference(root: Path, has_service: bool) -> None:
    if has_service:
        return
    build = (root / "build.gradle.kts").read_text(encoding="utf-8")
    require("dependsOn(commonMain, minecraft)" not in build, "has_service=false generated build must not reference minecraft in fabric common.")
    require("dependsOn(minecraft)" not in build, "has_service=false generated build must not reference minecraft target.")

def main() -> None:
    for language in ("java", "kotlin"):
        for has_service in (False, True):
            for root in generated(language, has_service):
                assert_language_cleanup(root, language, has_service)
                assert_service_split(root, has_service)
                assert_entrypoints_and_metadata(root, language)
                assert_no_service_false_minecraft_reference(root, has_service)
if __name__ == "__main__":
    main()
