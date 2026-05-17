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
    build = read("build.gradle.kts.jinja")
    final_jar = read("buildSrc/src/main/kotlin/FinalJarDsl.kt")
    container = read("buildSrc/src/main/kotlin/ContainerDsl.kt")
    require_no_match(r"class\s+ForgeMetadataTransformer", build, "build.gradle.kts.jinja must not define ForgeMetadataTransformer directly.")
    require_no_match(r"shadowMergedDevJar|shadowMergedJar|shadowSourcesJar", build, "build.gradle.kts.jinja must not register final jar aggregation tasks directly.")
    require_match(r"configureFinalJar\(", build, "build.gradle.kts.jinja must call configureFinalJar(...) from buildSrc.")
    require_match(r"class\s+ForgeMetadataTransformer", final_jar, "FinalJarDsl.kt must own Forge metadata merging.")
    require_match(r"shadowMergedDevJar", final_jar, "FinalJarDsl.kt must register merged dev jar.")
    require_match(r"shadowMergedJar", final_jar, "FinalJarDsl.kt must register merged release jar.")
    require_match(r"shadowSourcesJar", final_jar, "FinalJarDsl.kt must register merged sources jar.")
    require_match(r"runtimeElementsConfiguration\.apply", final_jar, "FinalJarDsl.kt must replace runtimeElements artifacts.")
    require_match(r"withVariantsFromConfiguration\([^)]*shadowRuntimeElementsConfiguration", final_jar, "FinalJarDsl.kt must skip shadow runtime variants.")
    require_match(r"filter\(MinecraftTarget::isVersionTarget\)", final_jar, "FinalJarDsl.kt must skip version target variants.")
    require_match(r"mergeServiceFiles\(\)", final_jar, "Final jars must merge service files.")
    require_match(r"filesMatching\(\"\*\*/\*\.class\"\).*DuplicatesStrategy\.EXCLUDE", final_jar, "Final jars must exclude duplicate class files.")
    require_match(r"fun\s+Project\.container\(", container, "Container DSL must expose Project.container.")
    require_match(r"fun\s+includeTarget\(target:\s*MinecraftTarget\)", container, "Container DSL must include target jars through includeTarget.")
    require_match(r"fun\s+embed\(", container, "Container DSL must expose embed wiring.")
    require_match(r"outgoing\.capability\(containerCapability\)", container, "Container runtime variants must publish loader-specific capability.")
if __name__ == "__main__":
    main()
