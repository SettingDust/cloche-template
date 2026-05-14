# Sync Developing Diff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synchronize the template with the current developing-repository build logic changes, sync the related docs, and remove unnecessary .jinja suffixes from static files.

**Architecture:** Treat D:\Projects\Minecraft\cloche-template-developing as the behavior source for build logic and mirrored documentation. Port the concrete Kotlin DSL and buildSrc API changes into the template files, then rename verified static template files that contain no Jinja syntax and repair any references that still point at the old suffixed paths.

**Tech Stack:** Copier template, Gradle Kotlin DSL, buildSrc Kotlin sources, PowerShell smoke scripts, git diff

---

### Task 1: Sync upstream documentation context

**Files:**
- Modify: `docs/superpowers/specs/2026-05-13-multiversion-dependencies-design.md`
- Create or Modify: `docs/superpowers/plans/2026-05-13-multiversion-dependencies.md`

- [ ] **Step 1: Read the current local and upstream doc variants**

Run: `Get-Content docs\superpowers\specs\2026-05-13-multiversion-dependencies-design.md -Raw`
Expected: local spec content loads successfully.

Run: `Get-Content D:\Projects\Minecraft\cloche-template-developing\docs\superpowers\specs\2026-05-13-multiversion-dependencies-design.md -Raw`
Expected: upstream spec content loads successfully.

- [ ] **Step 2: Copy upstream doc changes into the local doc files**

For the spec file, align the content with the upstream version while preserving only repository-local path differences when necessary.

```md
# Multiversion Dependencies Design

## Goal

Refactor the multiversion dependency DSL so that:

- `MultiversionDependencies` is exposed as a project extension instead of a manually-instantiated local object.
- the primary registration style remains property delegates such as `val MultiversionDependencies.mixinextras by maven(...) { ... }`.
- the current `DependencySourceKind`, `VariantField`, and `VariantOverride` model is replaced with a simpler nullable override model built directly around `group`, `artifact`, and `version`.
```

For the plan file, create or update `docs/superpowers/plans/2026-05-13-multiversion-dependencies.md` to match the upstream build-logic implementation plan content for the same feature.

- [ ] **Step 3: Verify the synced docs now exist and contain the expected headings**

Run: `Select-String -Path docs\superpowers\specs\2026-05-13-multiversion-dependencies-design.md -Pattern '^# Multiversion Dependencies Design'`
Expected: one match.

Run: `Select-String -Path docs\superpowers\plans\2026-05-13-multiversion-dependencies.md -Pattern '^# '`
Expected: at least one heading match.

### Task 2: Port the root/settings/buildSrc behavior changes

**Files:**
- Modify: `build.gradle.kts.jinja`
- Modify: `settings.gradle.kts.jinja`
- Modify: `buildSrc/build.gradle.kts`
- Modify: `buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja`
- Modify: `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts`
- Modify: `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`
- Modify: `buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja`
- Modify: `buildSrc/src/main/kotlin/ClocheTemplatePresetConventions.kt`
- Modify: `buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja`
- Modify: `buildSrc/src/main/kotlin/CompatibilityRules.kt`
- Modify: `buildSrc/src/main/kotlin/ContainerDsl.kt`
- Modify: `buildSrc/src/main/kotlin/FinalJarDsl.kt`
- Modify: `buildSrc/src/main/kotlin/MinecraftVersions.kt`
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencies.kt`
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt`
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt`
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt`
- Modify: `buildSrc/src/main/kotlin/VersionMappings.kt`
- Modify: `gradle/multiversion-dependencies.gradle.kts.jinja`

- [ ] **Step 1: Copy the upstream package and import changes into buildSrc Kotlin sources**

Apply the new `package settingdust.cloche_template.buildsrc` declaration to the affected Kotlin source templates and update consumers to import from that package.

```kotlin
package settingdust.cloche_template.buildsrc
```

- [ ] **Step 2: Port the upstream multiversion dependency API changes**

Update the core dependency DSL so that direct resolution returns an `ExternalModuleDependency` and target-aware helper methods resolve from `MinecraftTarget` plus `Project`.

```kotlin
fun MultiversionDependencySpec.resolve(target: MinecraftTarget, project: Project): ExternalModuleDependency =
    resolve(target.multiversionLoader(), target.minecraftVersionEnum(), project)
```

- [ ] **Step 3: Port the upstream root build script call-site changes**

Replace the old `resolve(...).toDependency(project)` call sites with the new target-aware helpers and import the buildSrc package.

```kotlin
import settingdust.cloche_template.buildsrc.*

implementation(multiversionDependencies.mixinextras.resolve(this@forge, project))
modImplementation(multiversionDependencies.klf.resolve(this@forge, project))
```

- [ ] **Step 4: Port the upstream shared-default and settings changes**

Update the buildSrc preset helpers and `settings.gradle.kts.jinja` so old settings-side multiversion registrations are removed and shared defaults are applied through buildSrc helpers.

```kotlin
targets.applySharedTargetDefaults(project)
```

- [ ] **Step 5: Run the focused verification immediately after the first substantive edit batch**

Run: `pwsh -File scripts\test-multiversion-dependencies.ps1`
Expected: the script either passes or fails on a concrete outdated assertion that tells you what still needs updating.

### Task 3: Update validation and repair mismatches

**Files:**
- Modify: `scripts/test-multiversion-dependencies.ps1`
- Modify: any file from Task 2 that the focused verification proves still mismatched

- [ ] **Step 1: Replace stale assertions in the smoke script**

Update the script so it checks for the synchronized behavior instead of the old settings-side DSL expectations.

```powershell
if ($build -notmatch 'import settingdust\.cloche_template\.buildsrc\.\*') {
    throw 'build.gradle.kts.jinja must import buildSrc packaged helpers'
}

if ($build -notmatch 'multiversionDependencies\.mixinextras\.resolve\(this@forge, project\)') {
    throw 'build.gradle.kts.jinja must resolve mixinextras from the forge target context'
}
```

- [ ] **Step 2: Re-run the same focused verification**

Run: `pwsh -File scripts\test-multiversion-dependencies.ps1`
Expected: pass.

- [ ] **Step 3: If the script passes, run one broader structural check**

Run: `rg '\.jinja' copier.yml AGENTS.md README.md scripts docs build.gradle.kts.jinja settings.gradle.kts.jinja`
Expected: only still-valid `.jinja` references remain.

### Task 4: Remove .jinja suffixes from verified static files

**Files:**
- Rename: `.github/dependabot.yml`
- Rename: `.github/workflows/build.yml`
- Rename: `.github/workflows/dependency-submission.yml`
- Rename: `.github/workflows/publish.yml`
- Rename: `buildSrc/build.gradle.kts`
- Rename: `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts`
- Rename: `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`
- Rename: `buildSrc/src/main/kotlin/ClocheTemplatePresetConventions.kt`
- Rename: `buildSrc/src/main/kotlin/CompatibilityRules.kt`
- Rename: `buildSrc/src/main/kotlin/ContainerDsl.kt`
- Rename: `buildSrc/src/main/kotlin/FinalJarDsl.kt`
- Rename: `buildSrc/src/main/kotlin/MinecraftVersions.kt`
- Rename: `buildSrc/src/main/kotlin/MultiversionDependencies.kt`
- Rename: `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt`
- Rename: `buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt`
- Rename: `buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt`
- Rename: `buildSrc/src/main/kotlin/VersionMappings.kt`
- Modify: `copier.yml`
- Modify: docs or scripts that still reference the old suffixed names

- [ ] **Step 1: Rename only the verified static files**

Run the renames in one batch after the content sync is stable.

```powershell
Move-Item buildSrc\build.gradle.kts.jinja buildSrc\build.gradle.kts
Move-Item buildSrc\src\main\kotlin\MultiversionDependencies.kt buildSrc\src\main\kotlin\MultiversionDependencies.kt
```

- [ ] **Step 2: Update copier exclusions and docs to use the renamed paths**

Adjust any path-based exclusions or documentation references that still point at the `.jinja` names.

```yaml
_exclude:
  - buildSrc/src/main/kotlin/**/*.kt
```

- [ ] **Step 3: Verify no stale references to renamed paths remain**

Run: `rg 'buildSrc/.+\.jinja|\.github/.+\.jinja|MultiversionDependencies\.kt\.jinja|build\.gradle\.kts\.jinja' .`
Expected: no matches except intentionally templated files that still need the suffix.

### Task 5: Finish end-to-end verification

**Files:**
- Validate the edited repository state

- [ ] **Step 1: Run the multiversion dependency smoke script one final time**

Run: `pwsh -File scripts\test-multiversion-dependencies.ps1`
Expected: pass.

- [ ] **Step 2: Run one additional repository-level structural check**

Run: `git diff --stat`
Expected: changed files align with the planned sync surface and renamed static files appear without unexpected unrelated churn.
