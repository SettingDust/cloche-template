from __future__ import annotations
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)

def require_match(pattern: str, text: str, message: str) -> None:
    require(re.search(pattern, text, re.DOTALL) is not None, message)

def require_no_match(pattern: str, text: str, message: str) -> None:
    require(re.search(pattern, text, re.DOTALL) is None, message)

def main() -> None:
    required_files = [
        "buildSrc/src/main/kotlin/MinecraftVersions.kt",
        "buildSrc/src/main/kotlin/MultiversionDependencies.kt",
        "buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt",
        "buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt",
        "buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt",
        "buildSrc/src/main/kotlin/VersionMappings.kt",
    ]
    for relative in required_files:
        require((ROOT / relative).is_file(), f"Missing required multiversion dependency file: {relative}")
    build = read("build.gradle.kts.jinja")
    settings = read("settings.gradle.kts.jinja")
    base_plugin = read("buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts")
    versions = read("buildSrc/src/main/kotlin/MinecraftVersions.kt")
    mappings = read("buildSrc/src/main/kotlin/VersionMappings.kt")
    dependencies = read("buildSrc/src/main/kotlin/MultiversionDependencies.kt")
    delegates = read("buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt")
    resolution = read("buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt")
    require_match(r"import settingdust\.cloche_template\.buildsrc\.\*", build, "build.gradle.kts.jinja must import packaged buildSrc helpers.")
    require_match(r"createMultiversionDependencies\(\)", base_plugin, "Base plugin must create multiversionDependencies extension.")
    require_match(r"require\(groupResolver == null && artifactResolver == null && versionResolver == null\)", dependencies, "Context-free resolve(project) must fail when target context is required.")
    require_match(r"fun\s+MultiversionDependencySpec\.resolve\(target:\s*MinecraftTarget", resolution, "Target-context resolver extension must exist.")
    require_match(r"fun\s+MinecraftTarget\.multiversionLoader\(\)", resolution, "Targets must map to multiversion loaders.")
    for enum_name, mc_version in (("20_1", "1.20.1"), ("21_1", "1.21.1"), ("26_1", "26.1.2")):
        require_match(rf"`{enum_name}`\(\"{re.escape(mc_version)}\"\)", versions, f"MinecraftVersion must declare {mc_version}.")
        require(mc_version in build, f"build.gradle.kts.jinja must reference Minecraft {mc_version}.")
    for function_name in ("fabricApiVersion", "forgeLoaderVersion", "neoForgeLoaderVersion", "parchmentVersion"):
        require_match(rf"fun\s+String\.{function_name}\(\)", mappings, f"VersionMappings must define {function_name}.")
    for spec_name in ("mixinextras", "preloadingTricks", "fabricLanguageKotlin", "klf"):
        require_match(rf"val\s+MultiversionDependencies\.{spec_name}", delegates, f"Preset dependency {spec_name} must be declared.")
    require_match(r"multiversionDependencies\.mixinextras\.resolve\(this@forge, project\)", build, "Forge mixinextras must resolve from target context.")
    require_match(r"multiversionDependencies\.klf\.resolve\(this@forge, project\)", build, "Forge KLF must resolve from target context.")
    require_match(r"multiversionDependencies\.preloadingTricks\.resolve\(this@forge, project\)", build, "Forge preloadingTricks must resolve from target context.")
    require_no_match(r"catalog\.mixinextras|catalog\.klf|catalog\.preloadingTricks", build, "build.gradle.kts.jinja must not consume old catalog dependencies.")
    require_no_match(r"dependency\(\"mixinextras\"|dependency\(\"klf\"", settings, "settings.gradle.kts.jinja must not declare old multiversion catalog dependencies.")
if __name__ == "__main__":
    main()
