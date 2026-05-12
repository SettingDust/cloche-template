# Multiversion Dependencies Design

**Goal:** Replace the current settings-side multi-version dependency catalog DSL with a single buildSrc-hosted, strongly typed dependency registry that can resolve dependency variants from a `MinecraftTarget` context.

**Architecture:** Add a `multiversionDependencies` registry in generated `buildSrc` backed by a `NamedDomainObjectContainer<MultiversionDependencySpec>`. Use delegated registration syntax such as `val MultiversionDependencies.mixinextras by multiversionDependencies.modrinth(...) { ... }`. Keep source-specific defaults at the spec root, express variant selection through a single `resolve { loader, mcVersion -> ... }` lambda, and bridge resolved variants to Gradle `Dependency` objects from a `Project` context.

**Tech Stack:** Copier template, Gradle Kotlin DSL, buildSrc Kotlin sources, Cloche `MinecraftTarget`, Gradle dependency APIs

---

## Goals

- Keep the dependency rules in `buildSrc`, not in `settings.gradle.kts.jinja`.
- Preserve strong typing and code completion for declared multi-version dependencies.
- Allow plain Maven dependencies and Modrinth Maven dependencies under one consistent model.
- Resolve dependency variants from `MinecraftTarget` using only loader and Minecraft version.
- Support reusable resolver helpers for common version patterns instead of forcing all rules into nested DSL blocks.
- Fail fast when a target requires a variant but no rule matches.

## Non-Goals

- Recreate Gradle version-catalog code generation in `buildSrc`.
- Automatically generate arbitrary Kotlin properties from runtime registration names.
- Support dimensions beyond loader and Minecraft version in the first iteration.
- Migrate every existing dependency rule in one step.

---

## Core Model

### `MultiversionDependencies`

`MultiversionDependencies` is the top-level registry exposed from `buildSrc`.

- Backed by `NamedDomainObjectContainer<MultiversionDependencySpec>`.
- Owns delegated registration entry points:
  - `multiversionDependencies.maven(...)`
  - `multiversionDependencies.modrinth(...)`
- Intended to be consumed through explicitly declared delegated properties, for example:

```kotlin
val MultiversionDependencies.mixinextras by multiversionDependencies.modrinth(
    artifact = "mixinextras",
    version = "0.5.4",
) {
    resolve(loaderArtifactOverrides())
}
```

The property declaration is both the accessor definition and the registration site. The design does not attempt to auto-generate arbitrary accessors from registration names.

### `MultiversionDependencySpec`

Each registry entry is a `MultiversionDependencySpec`.

The spec contains:

- Source kind: Maven or Modrinth Maven
- Required source identity fields
- Default variant fields stored on the spec root
- Optional resolver lambda: `resolve { loader, mcVersion -> variant(...) }`

Default variant fields live directly on the spec root. There is no `default {}` block in the first design.

#### Maven spec required fields

- `group`
- `artifact`
- `version`

#### Modrinth spec required fields

- `artifact`
- `version`

For Modrinth Maven, `artifact` is the only required coordinate identifier. There is no separate `id` field in this design.

### `MinecraftVersion`

`MinecraftVersion` is an enum representing supported template target versions.

Enum constants use compact names:

- `20_1`
- `21_1`
- `26_1`

Each enum constant stores the full resolved Minecraft version string used by target declarations:

- `20_1 -> "1.20.1"`
- `21_1 -> "1.21.1"`
- `26_1 -> "26.1.2"`

This enum is the single source of truth for supported MC versions and is intended to replace target-declaration string literals over time.

### `ResolvedDependencyVariant`

The resolver returns a lightweight `ResolvedDependencyVariant`, not a Gradle implementation class.

First-iteration fields:

- `group: String?`
- `artifact: String`
- `version: String`

The resolved variant provides a conversion function in `Project` context, for example:

```kotlin
fun ResolvedDependencyVariant.toDependency(project: Project): Dependency
```

This keeps resolution logic decoupled from Gradle object creation while still allowing direct Gradle API interaction at the consumption boundary.

---

## Registration DSL

### Delegated registration is the primary registration style

The preferred declaration style is delegated property registration on `MultiversionDependencies`.

#### Maven example

```kotlin
val MultiversionDependencies.slf4j by multiversionDependencies.maven(
    group = "org.slf4j",
    artifact = "slf4j-api",
    version = "2.0.17",
)
```

#### Modrinth example

```kotlin
val MultiversionDependencies.mixinextras by multiversionDependencies.modrinth(
    artifact = "mixinextras",
    version = "0.5.4",
) {
    resolve { loader, mcVersion ->
        when (loader) {
            MinecraftModLoader.FABRIC -> variant(artifact = "mixinextras-fabric")
            MinecraftModLoader.FORGE -> variant(artifact = "mixinextras-forge")
            else -> variant()
        }
    }
}
```

### Constructor parameters are required fields

Required defaults are not configured inside the block. They are supplied as parameters to the registration entry point.

This keeps the registration call site self-validating and avoids runtime misconfiguration for missing required fields.

### Action block is optional

Both `maven(...)` and `modrinth(...)` accept an optional action block.

If the block is omitted:

- no resolver is registered
- the default variant is always used

This supports simple dependencies without unnecessary DSL overhead.

---

## Resolution Model

### Root fields are the default variant

The spec root stores the default variant fields.

Examples:

- Maven default coordinate: `group + artifact + version`
- Modrinth default coordinate: `artifact + version`

### `resolve` is the only variant-selection entry point

Variant selection is expressed through one optional resolver:

```kotlin
resolve { loader, mcVersion ->
    ...
}
```

The resolver receives:

- `loader: MinecraftModLoader`
- `mcVersion: MinecraftVersion`

It returns a `variant(...)` patch relative to the default variant.

### `variant()` semantics

`variant(...)` returns an override patch.

- `variant()` with no arguments means “use default values unchanged”
- `variant(artifact = "...")` means “override only artifact”
- `variant(version = "...")` means “override only version”

If no `resolve` block exists, resolution returns the default variant directly.

### Reusable resolver helpers

Common variant-selection rules should be expressed as reusable resolver helpers or constants and then passed to `resolve(...)`.

Example shape:

```kotlin
resolve(loaderVersionMcVersionPattern())
```

This avoids adding a second parallel DSL for version formatting and keeps `resolve` as the only rule entry point.

Reusable helpers are especially appropriate for Modrinth version strings such as:

- `"version-loader,mcVersion"`

---

## Consumption API

### Use `MinecraftTarget` as context directly

No dedicated `MultiversionDependencyContext` type is introduced.

Consumption helpers use `context(MinecraftTarget)` directly because the target already carries the required information.

The context extraction logic converts target state into:

- `MinecraftModLoader`
- `MinecraftVersion`

### Dependency collector integration

Add overloads that accept `MultiversionDependencySpec` in target context.

Representative shape:

```kotlin
context(MinecraftTarget)
fun ClocheDependencyHandler.modImplementation(spec: MultiversionDependencySpec)

context(MinecraftTarget)
fun DependencyCollector.modImplementation(spec: MultiversionDependencySpec)
```

Implementation flow:

1. Derive `loader` and `mcVersion` from the current `MinecraftTarget`
2. Call `spec.resolve(loader, mcVersion)`
3. Convert the resolved variant with `toDependency(project)`
4. Delegate to the existing Gradle/Cloche dependency API

This keeps build script usage short while preserving explicit target-based resolution.

---

## Validation And Errors

### Registration-time validation

Validation performed when the spec is configured:

- Maven specs require `group`, `artifact`, and `version`
- Modrinth specs require `artifact` and `version`
- Override patches must not contain invalid empty required values

### Resolution-time validation

Resolution rules:

- If `resolve` is missing, return the default variant
- If `resolve` exists and returns `variant()`, use the default variant
- If `resolve` exists and no rule matches the current target, throw an error

Required error details:

- dependency spec name
- source kind (`maven` or `modrinth`)
- current loader
- current `MinecraftVersion`
- guidance to manually select a variant or add a resolver rule

No silent fallback should hide a missing required rule.

---

## Migration Plan

The migration should be incremental.

### Phase 1

Implement the infrastructure and migrate two representative dependencies only:

- `mixinextras`
- `klf`

These cover the two most important shapes:

- loader-only branching
- loader plus MC-version branching

### Phase 2

After the infrastructure is validated, evaluate migration of:

- `preloadingTricks`
- simple Maven dependencies that benefit from centralized management
- any remaining settings-side multi-version dependency declarations

The design intentionally avoids a one-shot full migration.

---

## Open Constraints Confirmed In Design

- The registry remains in `buildSrc` only.
- The design does not depend on settings plugins or version-catalog code generation.
- Delegated registration is the primary registration style.
- The spec root holds default variant fields.
- `resolve` is the only variant rule entry point.
- Common rule patterns are shared through reusable resolver helpers.
- `MinecraftTarget` is the only required consumption context.
