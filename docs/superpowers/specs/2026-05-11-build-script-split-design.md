# Build Script Split Design

## Goal

Refactor the generated Gradle build layout so that:

- generated `build.gradle.kts` remains the visible source of truth for Cloche target topology
- shared implementation and repetitive conventions move into `buildSrc`
- Copier variables affect only a small number of entry decisions and project metadata values
- `buildSrc` keeps the full capability surface for all supported variants instead of being structurally pruned by template variables
- code completion and Kotlin DSL type checking continue to work well in both the root build script and extracted build logic

## Constraints

- The generated build must not become a black box behind a single opaque plugin.
- Cloche targets should remain explicitly declared in the root build script.
- A third high-level matrix DSL that generates all targets is out of scope.
- Prefixes for internal convention plugins and helpers should use `clocheTemplate`.
- The current `game` / `service` terminology should be replaced.
- The replacement terms should be fixed template vocabulary, not user-configurable aliases.
- `minecraft` is the preferred replacement for the current `game` concept.
- `bootstrap` is the preferred replacement for the current `service` concept.
- Metadata should be fillable through a helper function rather than repeating the whole metadata block inline.

## Chosen Direction

Use a hybrid design:

- keep explicit Cloche target declarations in the root build script
- move reusable implementation into `buildSrc`
- expose a small set of helper functions and convention plugins under the `clocheTemplate` prefix
- do not generate the full target graph through a replacement DSL

This is the "A absorbs B" direction discussed during brainstorming:

- explicit targets are preserved
- helper APIs reduce repetition
- conventions are centralized
- build logic is split without hiding the resulting topology

## Naming Model

### Plugin and helper prefix

Use `clocheTemplate` for internal convention plugins and support APIs.

Examples:

- `clocheTemplate.base`
- `clocheTemplate.language.kotlin`
- `clocheTemplate.language.java`
- `clocheTemplate.support`

### Source-set and target vocabulary

Replace the current conceptual names:

- `game` -> `minecraft`
- `service` -> `bootstrap`

Rationale:

- `minecraft` clearly communicates code that interacts with Minecraft runtime itself
- `bootstrap` clearly communicates code that interacts with loader or pre-Minecraft initialization phases
- these terms describe interaction surfaces rather than deployment sides

These names should be template conventions and appear directly in generated source layout and target names.

## Architecture

### 1. Root build script responsibilities

The generated root `build.gradle.kts` remains the orchestration layer.

It should continue to contain:

- explicit target declarations such as `common(...)`, `fabric(...)`, `forge(...)`, and `neoforge(...)`
- target relationships such as `dependsOn(...)`
- project-specific exceptions and custom tweaks
- minimal plugin application and helper calls

It should avoid containing:

- large support classes
- compatibility rule implementations
- repeated metadata boilerplate
- repeated loader default wiring
- repeated container packaging setup when it can be expressed as helper calls

### 2. buildSrc responsibilities

`buildSrc` becomes the implementation and conventions layer.

It should contain four categories of code.

#### Base conventions

Provide convention plugins for shared build setup.

Examples:

- `clocheTemplate.base`
- `clocheTemplate.language.kotlin`
- `clocheTemplate.language.java`

These cover:

- plugin application that is truly global or language-specific
- repositories
- common Gradle setup such as `group`, `version`, archive naming, and base defaults when appropriate

#### Support code

Move complex Kotlin implementation out of the root script into plain Kotlin sources under `buildSrc/src/main/kotlin`.

Examples:

- `ContainerScope`
- `container(...)` helper integration
- attribute compatibility rules
- task name helpers
- version lookup functions such as loader version mapping and API version mapping

This code should live in `.kt` files rather than precompiled script plugins when it is primarily library-like support code.

#### Target presets

Expose a small helper surface for applying conventions to the current target.

Examples:

- `commonDefaults()`
- `minecraftDefaults()`
- `bootstrapDefaults()`
- `fabricDefaults()`
- `forgeDefaults()`
- `neoforgeDefaults()`
- `attachContainer()` or equivalent focused helpers

These helpers should apply conventions to an already-declared target.

They should not create targets on behalf of the root script.

#### Metadata helper

Provide a helper such as `clocheTemplateMetadata()` callable from within the `cloche {}` block.

The helper should populate metadata from generated project properties, including:

- `id`
- `name`
- `description`
- `author`
- `license`
- `source`

The root script may still override or extend specific metadata afterwards if needed.

## Copier Interaction Model

Copier variables should not decide which implementation files exist inside `buildSrc`.

Instead, Copier should affect only:

- which convention plugins are applied in the root build script
- generated metadata property values
- explicit target declarations that differ by language or bootstrap support
- rendered helper calls where variation is part of project shape

This means:

- `buildSrc` always includes all supported loader and packaging capabilities
- template variables influence entry wiring, not capability existence
- the resulting generated project remains understandable because the final targets are still declared in the root script

## Example Shape of the Generated Root Script

Illustrative structure only:

```kotlin
plugins {
    id("clocheTemplate.base")
    id("clocheTemplate.language.kotlin")
}

cloche {
    clocheTemplateMetadata()

    val commonMain = common("common:main") {
        commonDefaults()
    }

    val minecraft201 = common("minecraft:20.1") {
        minecraftDefaults()
        dependsOn(commonMain)
    }

    val minecraft211 = common("minecraft:21.1") {
        minecraftDefaults()
        dependsOn(commonMain)
    }

    val fabric201 = fabric("fabric:20.1") {
        minecraftVersion = "1.20.1"
        fabricDefaults()
        dependsOn(commonMain, minecraft201)
    }

    val forgeBootstrap = forge("forge:bootstrap") {
        minecraftVersion = "1.20.1"
        bootstrapDefaults()
        dependsOn(commonMain)
    }
}
```

This shape preserves the visible target topology while extracting repeated logic.

## File-Level Split Plan

### Generated root files

Keep these as thin orchestration entry points:

- `build.gradle.kts.jinja`
- `settings.gradle.kts.jinja`
- `gradle.properties.jinja`

Repository planning and design documents under `docs/` are not part of generated project output and should remain excluded through Copier.

### buildSrc files

Add a generated `buildSrc` with at least:

- `buildSrc/build.gradle.kts`
- `buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja`
- `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`
- `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts`
- `buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja`
- `buildSrc/src/main/kotlin/ClocheTemplatePresets.kt`
- `buildSrc/src/main/kotlin/ContainerDsl.kt`
- `buildSrc/src/main/kotlin/CompatibilityRules.kt`
- `buildSrc/src/main/kotlin/VersionMappings.kt`

Exact filenames can change, but the split should separate:

- convention plugins
- metadata helper
- target preset helpers
- complex support code

## Migration Scope From Current Root Script

Move out of the current root build script:

- support classes and helper DSL implementation
- compatibility rule classes
- repeated version mapping helpers
- metadata boilerplate
- repeated loader defaults where the logic is stable across generated projects

Keep in the root build script:

- target declarations
- project topology
- explicit `dependsOn` structure
- version-specific structural differences
- project-specific custom logic that benefits from staying visible

## Non-Goals

The design intentionally does not:

- replace explicit Cloche targets with a matrix-expanding DSL
- make naming aliases configurable
- conditionally prune buildSrc implementation files based on Copier variables
- hide the target graph inside convention plugins

## Risks and Mitigations

### Risk: helper surface grows into a second DSL

Mitigation:

- restrict helper APIs to defaults and focused support behavior
- never let helpers create the full target graph implicitly

### Risk: buildSrc starts depending on template variables too heavily

Mitigation:

- keep variable-sensitive decisions in the root script where possible
- treat buildSrc as a stable capability layer

### Risk: extracted conventions become hard to discover

Mitigation:

- keep helper names direct and literal
- keep target declarations explicit in the root script
- document generated project structure in the template README if needed

## Implementation Follow-Up

The next implementation plan should cover:

1. adding generated `buildSrc` infrastructure
2. moving support code from the root script into Kotlin sources
3. adding convention plugins under the `clocheTemplate` prefix
4. introducing metadata and target preset helpers
5. renaming `game` / `service` structure to `minecraft` / `bootstrap`
6. slimming the root `build.gradle.kts.jinja` while preserving explicit targets
