# Sync Developing Diff Design

**Goal:** Synchronize the current template with the active uncommitted git diff from D:\Projects\Minecraft\cloche-template-developing, also align the relevant spec/plan documents requested by the user, and remove .jinja suffixes from template files that do not actually use Jinja syntax.

**Architecture:** Mirror the developing repository's current behavioral diff into the template sources rather than selectively reinterpreting it. Treat the developing repository as the source of truth for build logic structure, especially around the packaged buildSrc Kotlin sources, the multiversion dependency resolution API, and root-script integration points. Extend that synchronization to the repository documentation artifacts the user explicitly requested, then normalize file naming by removing .jinja from files that contain no template syntax so static files are no longer marked as templated. Keep validation focused on the existing PowerShell smoke checks and adjust those checks only where the synchronized behavior changes their assertions.

**Tech Stack:** Copier template, Gradle Kotlin DSL, buildSrc Kotlin sources, PowerShell verification scripts

---

## Scope

- Synchronize all template-mapped changes from the current git diff in D:\Projects\Minecraft\cloche-template-developing.
- Synchronize the relevant spec and plan documents from D:\Projects\Minecraft\cloche-template-developing into this repository when they correspond to the synced build-logic changes.
- Update matching .jinja files in this repository so generated files match the current developing repository behavior.
- Remove the .jinja suffix from files that do not contain Jinja syntax and update any template references that depend on those names.
- Update validation scripts that assert the old structure when the synchronized behavior intentionally changes those expectations.

## Out Of Scope

- Re-designing the multiversion dependency model beyond what the developing repository already changed.
- Keeping backward compatibility with the previous template behavior when that behavior diverges from the developing repository diff.
- Refactoring unrelated template files that are not part of the mapped upstream diff.

## Source Mapping Rules

- Use the current uncommitted diff in D:\Projects\Minecraft\cloche-template-developing as the authoritative source.
- Map each changed concrete file to the corresponding template file in this repository.
- Preserve template substitutions and existing Jinja conditionals while porting behavior.
- If the developing repository changed a generated Kotlin file that corresponds to a .jinja template here, apply the same semantic change to the template rather than copying literal rendered values blindly.
- Treat documentation synchronization as an explicit user-requested extension even when those docs are not part of the current upstream git diff.
- Only remove a .jinja suffix after verifying the file content contains no Jinja markers such as {{, {%, or {#.

## Planned Change Areas

### 1. Root Build Script Synchronization

Update [build.gradle.kts.jinja](build.gradle.kts.jinja) to match the developing repository's current root build logic.

This includes:

- Importing the packaged buildSrc helpers from the new buildSrc package namespace.
- Keeping multiversion dependency access through the buildSrc extension API rather than the older intermediate ResolvedDependencyVariant conversion flow.
- Replacing old dependency call sites that manually resolved loader and version pairs with the newer target-aware resolve helpers.
- Moving shared target-default application to the packaged buildSrc helper where the upstream diff now centralizes it.
- Syncing the legacy classpath dependency usage so preloading tricks and KLF are resolved through the same multiversion dependency API used upstream.

### 2. Settings Script Synchronization

Update [settings.gradle.kts.jinja](settings.gradle.kts.jinja) so it reflects the upstream removal of the previous multi-version dependency declaration surface from settings.

This includes:

- Retaining plugin management and version catalog entries that still exist upstream.
- Removing declarations that the upstream diff moved out of settings and into buildSrc-backed dependency presets.

### 3. buildSrc Packaging And API Synchronization

Update the buildSrc Kotlin templates under [buildSrc/src/main/kotlin](buildSrc/src/main/kotlin) to match the upstream structural and API changes.

This includes:

- Adding the package declaration settingdust.cloche_template.buildsrc to the affected Kotlin templates.
- Updating imports and consumers so root scripts refer to packaged helpers consistently.
- Synchronizing the multiversion dependency implementation to return ExternalModuleDependency directly from resolution instead of returning an intermediate resolved value that is later converted.
- Synchronizing delegate definitions and preset registrations, including the upstream treatment of mixinextras, preloadingTricks, fabricLanguageKotlin, and klf.
- Synchronizing target-default helper functions and collection-level application helpers now housed in buildSrc.
- Mirroring any upstream formatting-relevant Kotlin DSL shape changes only where needed to preserve behavior.

### 4. buildSrc Build Script Synchronization

Update [buildSrc/build.gradle.kts](buildSrc/build.gradle.kts) to reflect the upstream buildSrc compiler configuration.

This currently includes removing the explicit -Xcontext-parameters compiler option because the upstream diff removed it. If this creates a compilation failure in the template after synchronization, treat that as a verification finding and reassess rather than silently keeping the old flag.

### 5. Validation Script Synchronization

Update [scripts/test-multiversion-dependencies.ps1](scripts/test-multiversion-dependencies.ps1) so its assertions match the synchronized template behavior.

This includes:

- Replacing checks that expect the old settings-side registration or catalog call sites.
- Adding checks for the new root-build import and resolve call shapes where those are the critical synchronized behaviors.
- Keeping the script focused on structural verification rather than trying to re-implement Gradle behavior.

### 6. Spec And Plan Synchronization

Synchronize the relevant design and implementation documents under [docs/superpowers/specs](docs/superpowers/specs) and [docs/superpowers/plans](docs/superpowers/plans) with the developing repository where they describe the same build-logic work being mirrored into this template repository.

This includes:

- Comparing the current repository docs with the developing repository versions.
- Porting content changes that describe the synchronized build-logic direction.
- Avoiding unrelated documentation churn outside the build-logic sync scope.

### 7. Remove Unneeded .jinja Suffixes

Rename static template files that do not contain any Jinja syntax so they no longer use the .jinja suffix.

The currently identified candidates are:

- [.github/dependabot.yml](.github/dependabot.yml)
- [.github/workflows/build.yml](.github/workflows/build.yml)
- [.github/workflows/dependency-submission.yml](.github/workflows/dependency-submission.yml)
- [.github/workflows/publish.yml](.github/workflows/publish.yml)
- [buildSrc/build.gradle.kts](buildSrc/build.gradle.kts)
- [buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts](buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts)
- [buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts](buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts)
- [buildSrc/src/main/kotlin/ClocheTemplatePresetConventions.kt](buildSrc/src/main/kotlin/ClocheTemplatePresetConventions.kt)
- [buildSrc/src/main/kotlin/CompatibilityRules.kt](buildSrc/src/main/kotlin/CompatibilityRules.kt)
- [buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja](buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja)
- [buildSrc/src/main/kotlin/ContainerDsl.kt](buildSrc/src/main/kotlin/ContainerDsl.kt)
- [buildSrc/src/main/kotlin/FinalJarDsl.kt](buildSrc/src/main/kotlin/FinalJarDsl.kt)
- [buildSrc/src/main/kotlin/MinecraftVersions.kt](buildSrc/src/main/kotlin/MinecraftVersions.kt)
- [buildSrc/src/main/kotlin/MultiversionDependencies.kt](buildSrc/src/main/kotlin/MultiversionDependencies.kt)
- [buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt](buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt)
- [buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt](buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt)
- [buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt](buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt)
- [buildSrc/src/main/kotlin/VersionMappings.kt](buildSrc/src/main/kotlin/VersionMappings.kt)

This work also includes updating any copier exclusions, documentation, or validation scripts that refer to the old suffixed names.

## Implementation Strategy

1. Read the minimal set of corresponding template files for each upstream diff region.
2. Apply the upstream behavior into the template files with the smallest faithful edits.
3. Synchronize the relevant docs and then rename the verified static .jinja files while preserving repository structure and references.
4. Run the narrowest available verification immediately after the first substantive edit, starting with the multiversion dependency verification script because it directly covers the highest-risk synchronized area.
5. Repair any local mismatches revealed by that focused check before broadening to additional verification.
6. Finish with at least one executable validation pass covering the synchronized build logic surface and one structural check that no renamed static file is still referenced by its old .jinja path.

## Risks And Checks

- Package introduction risk: adding a package to buildSrc Kotlin templates requires all root script imports and cross-file references to stay consistent.
- Behavior drift risk: the current template contains a newer design layer around gradle/multiversion-dependencies.gradle.kts.jinja, and synchronizing upstream may invalidate assumptions in that file or its tests.
- Verification risk: the upstream diff removes a compiler flag that repository memory previously identified as necessary for context parameters; this must be verified empirically instead of assumed safe.
- Rename risk: removing .jinja suffixes can break copier behavior or repository references if any path, exclude rule, or documentation still expects the old filenames.
- Documentation scope risk: the developing repository docs are not part of the active upstream diff, so doc synchronization must remain tightly scoped to the same build-logic changes instead of copying unrelated edits.

## Success Criteria

- The template's mapped .jinja files reflect the current behavior of the developing repository diff.
- The requested spec and plan files are synchronized where they describe the same mirrored change set.
- Verified static files no longer carry a .jinja suffix, and no repository references remain to their previous suffixed names.
- The old settings-side multiversion dependency assertions are removed or replaced where upstream behavior changed.
- The targeted multiversion dependency verification script passes after synchronization, or any remaining failure is isolated and explicitly reported.