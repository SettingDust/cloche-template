# Multiversion Dependencies Design

## Goal

Refactor the multiversion dependency DSL so that:

- `MultiversionDependencies` is exposed as a project extension instead of a manually-instantiated local object.
- the primary registration style remains property delegates such as `val MultiversionDependencies.mixinextras by maven(...) { ... }`.
- the current `DependencySourceKind`, `VariantField`, and `VariantOverride` model is replaced with a simpler nullable override model built directly around `group`, `artifact`, and `version`.

## Current Problems

1. The current entry point is a local object created in `build.gradle.kts` instead of a reusable Gradle extension.
2. `DependencySourceKind` only exists to let delegate factories apply different defaults, but that concern leaks into resolution.
3. `VariantField.Keep` and `VariantField.Set` add an extra abstraction layer for a problem that is only "override this field or keep the base value".
4. Registration currently depends on delegate-backed lazy creation, which makes lifecycle and initialization less explicit than they should be.

## Design Summary

The refactor keeps the current mental model:

- declare named dependency specs on `MultiversionDependencies`
- resolve them for `(loader, minecraftVersion)`
- turn the resolved variant into a Gradle dependency

The internal representation is simplified to:

- a base `group`, `artifact`, and `version` stored on `MultiversionDependencySpec`
- a resolver that returns nullable overrides for those same three fields
- a merge step where `null` means "keep the base value" and non-null means "override"

## Architecture

### Project Extension

Add a project-level extension that mirrors the existing pattern used by preset conventions:

- `val Project.multiversionDependencies: MultiversionDependencies`
- `fun Project.createMultiversionDependencies()`
- `fun Project.multiversionDependencies(configure: MultiversionDependencies.() -> Unit)`

`MultiversionDependencies` should continue to wrap and delegate to `NamedDomainObjectContainer<MultiversionDependencySpec>`, because the requested DSL requires registration and lookup behavior on the same object.

This keeps the extension usable as both:

- a standard Gradle extension entry point
- the receiver for delegate-based registration helpers

### Registration DSL

There are two registration contexts with different syntax, but the same underlying delegate provider mechanism.

**buildSrc preset declarations** (infrastructure only, not modified by users)

Used inside `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt` to define well-known presets that every project gets:

```kotlin
val MultiversionDependencies.mixinextras by maven(
    group = "io.github.llamalad7",
    artifact = "mixinextras-common",
    version = "0.5.4"
) {
    resolve { loader, mcVersion ->
        variant(artifact = "...")
    }
}
```

Here the delegate receiver is `MultiversionDependencies` and the result becomes a typed extension property accessible as `multiversionDependencies.mixinextras`.

**Build script declarations** (project-specific, modified by users)

Used at the top level of `build.gradle.kts` (or an included `.gradle.kts` script) with the same extension property syntax:

```kotlin
val MultiversionDependencies.myDep by maven(
    group = "com.example",
    artifact = "my-lib",
    version = "1.0"
) {
    resolve { loader, mcVersion ->
        variant(version = "...")
    }
}
```

The syntax is identical to buildSrc preset declarations. The difference is only in which file the declaration lives. Accessing the spec uses `multiversionDependencies.myDep`.

This means:

- `maven(...)` and `modrinth(...)` remain extension functions on `MultiversionDependencies`
- they continue returning `PropertyDelegateProvider<MultiversionDependencies, ReadOnlyProperty<MultiversionDependencies, MultiversionDependencySpec>>`
- they register or retrieve named specs through the wrapped `NamedDomainObjectContainer`
- the delegate mechanism is identical in both contexts; only the receiver binding site differs

### Simplified Variant Model

Remove these public concepts:

- `DependencySourceKind`
- `VariantField`
- `VariantOverride`

Replace them with a single thin override carrier built around the same three dependency coordinates. The implementation may use a very small data class for readability, but it must not introduce extra state beyond nullable `group`, `artifact`, and `version`.

Recommended shape:

```kotlin
data class DependencyVariant(
    val group: String? = null,
    val artifact: String? = null,
    val version: String? = null,
)
```

`MultiversionResolver` remains a `(MinecraftModLoader, MinecraftVersion) -> DependencyVariant`.

`variant(group, artifact, version)` remains as a convenience helper, but it now just returns the thin override carrier with nullable fields.

### Source-Specific Defaults

`DependencySourceKind` is not needed once source behavior is expressed directly in registration helpers.

The split becomes:

- `maven(...)` writes the supplied `group`, `artifact`, and `version` directly onto the base spec
- `modrinth(...)` sets `group = "maven.modrinth"` and fills the remaining base coordinates directly

Resolution should no longer branch on source kind.

### Resolution Flow

`MultiversionDependencySpec.resolve(loader, mcVersion)` should work as follows:

1. Start from the spec's base `group`, `artifact`, and `version`
2. Invoke the resolver if present
3. For each field:
   - use the override value when it is non-null
   - otherwise keep the base value
4. Validate the final result
5. Return `ResolvedDependencyVariant`

This removes the need for `resolveOr` and for the unchecked cast currently needed by `VariantField.Set`.

## Initialization Strategy

The extension itself is created explicitly. Build-script declarations run eagerly during configuration, so their specs are registered at the point the `multiversionDependencies { }` block executes.

Preset specs declared in buildSrc as extension properties (`val MultiversionDependencies.mixinextras by maven { ... }`) are lazy by design and only register on first access, which is fine because they are accessed explicitly by callers in the build script.

Expected behavior:

- `createMultiversionDependencies()` creates the extension if absent; called from a convention plugin or the build script early in configuration
- all specs (both preset and project-specific) are registered lazily on first access through their extension property delegate
- no explicit-materialization step is needed, because every spec is accessed through a typed extension property before resolution

## File-Level Changes

### Core model

Update `buildSrc/src/main/kotlin/MultiversionDependencies.kt`:

- remove `DependencySourceKind`
- remove `VariantField`
- remove `VariantOverride`
- introduce the thin nullable override carrier
- update `MultiversionResolver`
- update `MultiversionDependencySpec.resolve(...)`
- keep `ResolvedDependencyVariant` as the final validated result

### Delegate factories

Update `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt`:

- remove source-kind assignment
- set base coordinates directly in `maven(...)`
- set the modrinth default group directly in `modrinth(...)`
- keep delegate-based registration API intact
- keep preset spec declarations (`mixinextras`, `klf`) here, as these are infrastructure-level presets not expected to be modified by users

### Helper patterns

Update `buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt`:

- return the new thin override carrier instead of `VariantOverride`
- keep current behavior unchanged

### Extension API

Add project extension helpers in either `buildSrc/src/main/kotlin/MultiversionDependencies.kt` or a dedicated adjacent file:

- create extension if absent
- expose typed accessors from `Project`
- provide a configuration helper

### Build script adoption

Update `build.gradle.kts`:

- remove manual `objects.newInstance(...)`
- create the extension through the project helper
- consume the extension through `project.multiversionDependencies`

### Remove gradle/dependencies.gradle.kts

Delete `gradle/dependencies.gradle.kts`.

This file currently uses the old `apply(from = ...)` script-plugin pattern and manually calls `maybeCreate(...)` inside a `with(multiversionDependencies)` block. The two dependency registrations it contains (`mixinextras` and `klf`) will move to preset extension property declarations in `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt`. Any future project-specific dependency registrations belong in the `multiversionDependencies { }` block inside `build.gradle.kts` directly, without any `apply(from = ...)`.

## Error Handling

Validation remains in `MultiversionDependencySpec.resolve(...)` and should continue failing fast when:

- `artifact` resolves blank
- `version` resolves blank
- `group` resolves blank

The error messages should continue to include the dependency name, loader, and Minecraft version.

## Testing Strategy

Focus verification on behavior, not on implementation details.

Required cases:

1. Maven registration keeps explicit base coordinates unchanged when no override is returned.
2. Modrinth registration defaults the group to `maven.modrinth`.
3. Nullable override semantics work:
   - `null` keeps the base value
   - non-null replaces the base value
4. Validation still fails for blank final coordinates.
5. Existing helper resolvers in `buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt` still produce the same resolved coordinates as before.

The first validation command after implementation should be the narrowest available Gradle or Kotlin compilation/test command that covers `buildSrc` and the touched DSL code.

## Migration Notes

Migration should be incremental:

1. Introduce the extension API
2. Switch the build script to use it
3. Simplify the core model to nullable overrides
4. Update delegate factories and pattern helpers
5. Run narrow validation on the touched build logic

This order keeps extension wiring and resolver semantics separable while refactoring.

## Non-Goals

- Replacing delegate-based registration with a new container DSL
- Expanding the dependency model beyond `group`, `artifact`, and `version`
- Broad refactoring outside multiversion dependency registration and resolution
- Keeping `gradle/dependencies.gradle.kts`: this file will be deleted as part of the migration
