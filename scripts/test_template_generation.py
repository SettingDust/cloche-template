from __future__ import annotations
from pathlib import Path
from testlib import generated_project, require


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

def assert_template_artifacts_excluded(root: Path) -> None:
    for relative in ("AGENTS.md", "SPEC.md", "scripts", "docs", "copier.yml", "copier.yaml"):
        require(not (root / relative).exists(), f"Generated project must not include template-only artifact {relative}.")

def main() -> None:
    for language in ("java", "kotlin"):
        for has_service in (False, True):
            with generated_project(language, has_service) as root:
                assert_language_cleanup(root, language, has_service)
                assert_service_split(root, has_service)
                assert_entrypoints_and_metadata(root, language)
                assert_no_service_false_minecraft_reference(root, has_service)
                assert_template_artifacts_excluded(root)
if __name__ == "__main__":
    main()
