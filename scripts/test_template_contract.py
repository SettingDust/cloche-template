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

def assert_no_deleted_file_references() -> None:
    build = read("build.gradle.kts.jinja")
    settings = read("settings.gradle.kts.jinja")
    multiversion_script = ROOT / "gradle/multiversion-dependencies.gradle.kts.jinja"
    require(not multiversion_script.exists(), "Deleted multiversion dependency Gradle script must stay deleted.")
    require_no_match(
        r"gradle/multiversion-dependencies\.gradle\.kts",
        build + "\n" + settings,
        "Templates must not reference deleted gradle/multiversion-dependencies.gradle.kts.",
    )

def assert_no_service_false_minecraft_reference() -> None:
    build = read("build.gradle.kts.jinja")
    service_false_refs = [
        r"\{%-\s*else\s*%\}\s*dependsOn\([^\n)]*minecraft",
        r"\{%\s*if\s+not\s+has_service\s*%\}.*minecraft",
    ]
    for pattern in service_false_refs:
        require_no_match(pattern, build, "has_service=false build branch must not reference minecraft targets.")

def assert_language_convention_entrypoints() -> None:
    kotlin_plugin = read("buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts")
    java_plugin = read("buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts")
    for loader in ("fabric", "forge", "neoforge"):
        require_match(loader, kotlin_plugin, f"Kotlin language plugin must configure {loader} conventions.")
        require_match(loader, java_plugin, f"Java language plugin must configure {loader} conventions.")
    require_match(r"adapter\.set\(\"kotlin\"\)", kotlin_plugin, "Kotlin Fabric entrypoints must use Kotlin adapter.")
    require_match(r"modLoader\.set\(\"klf\"\)", kotlin_plugin, "Kotlin Forge-like metadata must use KLF loader.")
    require_match(r"entrypoint\(\"main\"", java_plugin, "Java Fabric main entrypoint must be configured.")
    require_match(r"modLoader\.set\(\"javafml\"\)", java_plugin, "Java Forge-like metadata must use javafml loader.")

def assert_java_templates_have_no_same_name_import_collisions() -> None:
    for path in (ROOT / "src").rglob("*.java.jinja"):
        text = path.read_text(encoding="utf-8")
        package_match = re.search(r"^package\s+([\w{}.]+);", text, re.MULTILINE)
        class_match = re.search(r"\b(?:class|interface|enum|record)\s+([A-Za-z_]\w*)\b", text)
        if not package_match or not class_match:
            continue
        declared_name = class_match.group(1)
        declared_package = package_match.group(1)
        require_no_match(
            rf"^import\s+{re.escape(declared_package)}\.{declared_name};",
            text,
            f"{path.relative_to(ROOT)} imports its own declared type.",
        )
        require_no_match(
            rf"^import\s+[\w{{}}.]+\.{declared_name};\s*\n\s*public\s+(?:class|interface|enum|record)\s+{declared_name}\b",
            text,
            f"{path.relative_to(ROOT)} has same-simple-name import collision.",
        )

def assert_post_gen_uses_rendered_paths() -> None:
    post_gen = read(".copier/tasks/post_gen.py.jinja")
    require_no_match(
        r"IdentifierFactory[^\n]+\.jinja|MinecraftAdapter[^\n]+\.jinja",
        post_gen,
        "post_gen must move rendered files without .jinja suffix.",
    )

def main() -> None:
    assert_no_deleted_file_references()
    assert_no_service_false_minecraft_reference()
    assert_language_convention_entrypoints()
    assert_java_templates_have_no_same_name_import_collisions()
    assert_post_gen_uses_rendered_paths()
if __name__ == "__main__":
    main()
