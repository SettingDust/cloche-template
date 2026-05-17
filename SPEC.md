# SPEC
§G
生成 Cloche Minecraft mod Copier template；支持 Fabric/Forge/NeoForge、多 MC 版本、Java/Kotlin、?bootstrap service split。
§C
C1: template engine = Copier + Jinja2.
C2: build = Gradle Kotlin DSL + buildSrc precompiled/convention plugins.
C3: Cloche plugin version 0.18.11-dust.18.
C4: buildSrc Kotlin toolchain = 25.
C5: generated mod language ∈ {kotlin, java}.
C6: supported MC targets = 1.20.1, 1.21.1, 26.1.2.
C7: supported loaders = fabric, forge, neoforge.
C8: bootstrap layer Java-only.
C9: generated project initialized with git by Copier tasks.
C10: tests ! contract-oriented, not script-by-script migration.
§I
cfg: `copier.yml` → vars `name,id,slug,description,author,group,license,has_service,language`.
cmd: `copier copy . <dest>` → generated mod project.
cmd: `copier update` → update generated project.
task: `.copier/tasks/post_gen.py` → migrate/remove language/service-specific files.
cmd: `./gradlew build` in generated project → final jars + sources jar.
cmd: `./gradlew runClient` / `./gradlew runServer` in generated project → dev runs.
cmd: `pwsh ./scripts/test-buildsrc-presets.ps1` → preset smoke check.
cmd: `pwsh ./scripts/test-final-jar-buildsrc.ps1` → final-jar smoke check.
cmd: `pwsh ./scripts/test-multiversion-dependencies.ps1` → multiversion dependency smoke check.
cmd: `python scripts/test_buildsrc_presets.py` → preset smoke check.
cmd: `python scripts/test_final_jar_buildsrc.py` → final-jar smoke check.
cmd: `python scripts/test_multiversion_dependencies.py` → multiversion dependency smoke check.
cmd: `python scripts/test_template_generation.py` → Copier generation matrix check.
cmd: `python scripts/test_generated_builds.py` → generated-project Gradle build check.
api: `clocheTemplatePresetConventions { fabric|forge|neoforge { ... }` → language/plugin target conventions.
api: `multiversionDependencies.<spec>.resolve(target, project)` → dependency variant resolution.
api: `project.container(loader) { includeTarget/embed/jar }` → loader container jars.
§V
V1: `copier.yml` validators ! enforce `name,id,slug,group` shape before render.
V2: `language=java` → generated `src/**/main/kotlin` absent.
V3: `language=kotlin && has_service=false` → generated `src/**/main/java` absent.
V4: `has_service=false` → generated `src/forge/bootstrap`, `src/neoforge/bootstrap`, `src/minecraft` absent.
V5: `has_service=true` → `IdentifierFactory` + `MinecraftAdapter` impl/services moved from `src/common/{20.1,21.1,26.1}` to `src/minecraft/{20.1,21.1,26.1}`.
V6: bootstrap targets ! contain Java sources only; `src/*/bootstrap/**/main/kotlin` absent.
V7: Fabric targets cover 1.20.1, 1.21.1, 26.1.2.
V8: Forge minecraft target covers 1.20.1.
V9: NeoForge minecraft targets cover 1.21.1, 26.1.2.
V10: version targets disable manifest/jar/remap/include tasks via buildSrc defaults.
V11: language plugins ! register loader entrypoints + loader metadata via `clocheTemplatePresetConventions`.
V12: final build ! emits merged dev jar, remapped jar, sources jar through `configureFinalJar`.
V13: container jars ! merge service files; duplicate `.class` excluded.
V14: `MultiversionDependencySpec.resolve(project)` ! fail if target context required.
V15: unsupported MC version string → `MinecraftVersion.fromValue` fail fast.
V16: public dependency variants skip version target api/runtime variants from Maven publication.
V17: generated metadata ! include mod id, name, description, license, icon, source, issues, author, minecraft dependency.
V18: build scripts ! use packaged buildSrc helpers, not copied ad-hoc Gradle scripts.
V19: repository smoke scripts ! assert buildSrc preset/final-jar/multiversion contracts.
V20: ? `gradle/multiversion-dependencies.gradle.kts.jinja` expected by smoke script but absent in repo.
V21: `has_service=false` → generated `build.gradle.kts` ⊥ reference `minecraft` target.
V22: repository test logic ! live in Python scripts; PowerShell wrappers ? delegate only.
V23: static template contract ! catch stale refs, invalid Jinja branches, Java same-name import collisions, deleted-file refs.
V24: Copier render contract ! run matrix `language ∈ {java,kotlin}` × `has_service ∈ {false,true}` without Gradle.
V25: generated build contract ! slow; compile only representative combos `java+has_service=false`, `kotlin+has_service=true`.
V26: packaging contract ! assert final jar/container/runtime variant wiring statically, separate from render/build matrix.
V27: multiversion dependency contract ! assert helper files, resolver fail-fast, loader/version mappings, MC version refs aligned.
§T
id|status|task|cites
T1|x|Fix/confirm missing `gradle/multiversion-dependencies.gradle.kts.jinja` smoke expectation|V20,I.cmd
T2|x|Add generation matrix smoke test for `language` × `has_service` cleanup|V2,V3,V4,V5,V6,I.task
T3|x|Add generated-project build smoke for at least kotlin+service and java+no-service|V7,V8,V9,V12,V21,I.cmd
T4|x|Add assertions for generated entrypoint/service files per loader/language|V11,V17
T5|x|Document or test MC 26.1.2 mapping/loader dependency policy|V7,V9,V15
T6|x|Replace PowerShell smoke scripts with Python contract tests, not mechanical ports|V19,V22,V23,V24,V25,V26,V27,I.cmd
T7|x|Create static template contract test for stale refs/Jinja branches/Java naming collisions|V21,V23,I.cmd
T8|x|Create Copier render contract test for full `language` × `has_service` matrix|V2,V3,V4,V5,V6,V11,V17,V21,V24,I.cmd
T9|x|Create generated build contract test for representative slow combos|V7,V8,V9,V12,V25,I.cmd
T10|x|Create packaging contract test for final jar/container/runtime variant wiring|V12,V13,V16,V26,I.cmd
T11|x|Create multiversion dependency contract test for resolver/mapping/MC refs|V14,V15,V18,V27,I.cmd
T12|x|Delete old PowerShell test scripts after Python contracts pass|V22,I.cmd
§B
id|date|cause|fix
B1|2026-05-17|no-service generated build referenced undeclared `minecraft` target|V21
