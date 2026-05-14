# Multiversion Dependencies Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the manually-instantiated `MultiversionDependencies` local variable and the `DependencySourceKind / VariantField / VariantOverride` model with a Gradle project extension and a simple nullable-override variant model.

**Architecture:** `MultiversionDependencies` becomes a real Gradle project extension exposing a `NamedDomainObjectContainer<MultiversionDependencySpec>`. Specs are registered via property delegates (`val MultiversionDependencies.foo by maven(...)`). The variant model is replaced by a thin `DependencyVariant(group?, artifact?, version?)` data class; resolution merges base coordinates with nullable overrides.

**Tech Stack:** Kotlin, Gradle Kotlin DSL, `org.gradle.api.Project` extension API, `NamedDomainObjectContainer`.

**Critical design constraint for delegates:** `maven(...)` and `modrinth(...)` must be top-level free functions (not extension functions on `MultiversionDependencies`), so they are callable in a top-level `val MultiversionDependencies.foo by maven(...)` declaration where no `MultiversionDependencies` receiver is in scope. `RegisteredSpecDelegate` must use the `thisRef` parameter of `getValue(thisRef, property)` — not a captured `container` — because top-level extension property delegates are initialized statically and `provideDelegate` receives `null` as `thisRef`.

---

### Task 1: Simplify the core model in MultiversionDependencies.kt

**Files:**
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencies.kt`

- [ ] **Step 1: Replace the three removed types and update the core model**

  Open `buildSrc/src/main/kotlin/MultiversionDependencies.kt`. Replace the entire file content with:

  ```kotlin
  import earth.terrarium.cloche.api.attributes.MinecraftModLoader
  import org.gradle.api.Named
  import org.gradle.api.NamedDomainObjectContainer
  import org.gradle.api.Project
  import org.gradle.api.artifacts.Dependency
  import org.gradle.kotlin.dsl.the
  import javax.inject.Inject

  data class DependencyVariant(
      val group: String? = null,
      val artifact: String? = null,
      val version: String? = null,
  )

  data class ResolvedDependencyVariant(
      val group: String,
      val artifact: String,
      val version: String,
  )

  typealias MultiversionResolver = (MinecraftModLoader, MinecraftVersion) -> DependencyVariant

  open class MultiversionDependencySpec @Inject constructor(
      private val dependencyName: String,
  ) : Named {
      var group: String? = null
      var artifact: String = dependencyName
      var version: String = ""

      private var resolver: MultiversionResolver? = null

      override fun getName(): String = dependencyName

      fun resolve(block: MultiversionResolver) {
          resolver = block
      }

      fun variant(
          group: String? = null,
          artifact: String? = null,
          version: String? = null,
      ): DependencyVariant = DependencyVariant(group = group, artifact = artifact, version = version)

      fun resolve(loader: MinecraftModLoader, mcVersion: MinecraftVersion): ResolvedDependencyVariant {
          val patch = resolver?.invoke(loader, mcVersion) ?: DependencyVariant()
          val resolvedGroup = patch.group ?: group
          val resolvedArtifact = patch.artifact ?: artifact
          val resolvedVersion = patch.version ?: version

          require(resolvedArtifact.isNotBlank()) {
              "Dependency $name resolved an empty artifact for $loader / $mcVersion"
          }
          require(resolvedVersion.isNotBlank()) {
              "Dependency $name resolved an empty version for $loader / $mcVersion"
          }
          require(!resolvedGroup.isNullOrBlank()) {
              "Dependency $name requires a group for $loader / $mcVersion"
          }

          return ResolvedDependencyVariant(
              group = resolvedGroup!!,
              artifact = resolvedArtifact,
              version = resolvedVersion,
          )
      }
  }

  open class MultiversionDependencies @Inject constructor(
      val project: Project,
      private val entries: NamedDomainObjectContainer<MultiversionDependencySpec>,
  ) : NamedDomainObjectContainer<MultiversionDependencySpec> by entries

  private const val EXTENSION_NAME = "multiversionDependencies"

  val Project.multiversionDependencies: MultiversionDependencies
      get() = the()

  fun Project.createMultiversionDependencies() {
      if (extensions.findByName(EXTENSION_NAME) == null) {
          val instance = objects.newInstance(
              MultiversionDependencies::class.java,
              this,
              objects.domainObjectContainer(MultiversionDependencySpec::class.java),
          )
          extensions.add(MultiversionDependencies::class.java, EXTENSION_NAME, instance)
      }
  }

  fun Project.multiversionDependencies(configure: MultiversionDependencies.() -> Unit) {
      multiversionDependencies.configure()
  }

  fun ResolvedDependencyVariant.toDependency(project: Project): Dependency =
      project.dependencies.create("$group:$artifact:$version")
  ```

- [ ] **Step 2: Verify buildSrc compiles**

  Run: `./gradlew buildSrc:compileKotlin`

  Expected: BUILD SUCCESSFUL with no errors.

---

### Task 2: Rewrite MultiversionDependencyDelegates.kt

**Files:**
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt`

Key changes from the current file:
- `RegisteredSpecDelegate` uses `thisRef.maybeCreate(property.name)` in `getValue`, **not** a captured `container`. This is required because top-level extension property delegates are initialized statically; the `thisRef` passed to `provideDelegate` is `null` for top-level extension properties.
- `PropertyDelegateProvider` wrapper is removed. `maven(...)` and `modrinth(...)` return `ReadOnlyProperty<MultiversionDependencies, MultiversionDependencySpec>` directly.
- `maven(...)` and `modrinth(...)` become top-level free functions (not extension functions). This allows `val MultiversionDependencies.foo by maven(...)` to compile at the top level of any file where no `MultiversionDependencies` receiver is available.
- Preset declarations for `mixinextras` and `klf` move here from `gradle/dependencies.gradle.kts`.

- [ ] **Step 1: Replace the entire file**

  Replace the entire content of `buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt` with:

  ```kotlin
  import earth.terrarium.cloche.api.attributes.MinecraftModLoader
  import kotlin.properties.ReadOnlyProperty
  import kotlin.reflect.KProperty

  private class RegisteredSpecDelegate(
      private val configure: MultiversionDependencySpec.() -> Unit,
  ) : ReadOnlyProperty<MultiversionDependencies, MultiversionDependencySpec> {
      private var cached: MultiversionDependencySpec? = null

      override fun getValue(
          thisRef: MultiversionDependencies,
          property: KProperty<*>,
      ): MultiversionDependencySpec {
          return cached ?: thisRef.maybeCreate(property.name).apply(configure).also { cached = it }
      }
  }

  fun maven(
      group: String,
      artifact: String,
      version: String,
      action: MultiversionDependencySpec.() -> Unit = {},
  ): ReadOnlyProperty<MultiversionDependencies, MultiversionDependencySpec> =
      RegisteredSpecDelegate {
          this.group = group
          this.artifact = artifact
          this.version = version
          action()
      }

  fun modrinth(
      artifact: String,
      version: String,
      action: MultiversionDependencySpec.() -> Unit = {},
  ): ReadOnlyProperty<MultiversionDependencies, MultiversionDependencySpec> =
      RegisteredSpecDelegate {
          this.group = "maven.modrinth"
          this.artifact = artifact
          this.version = version
          action()
      }

  // Preset specs — infrastructure-level, not modified by users.
  // Registration is lazy: the spec is created in the container on first property access.
  // Inside the action lambda the receiver is MultiversionDependencySpec, so `resolve` and
  // `variant` are both in scope. The inner resolver lambda captures `this: MultiversionDependencySpec`
  // from the outer action scope, so `variant(...)` is also accessible inside the resolver.

  val MultiversionDependencies.mixinextras: MultiversionDependencySpec by modrinth(
      artifact = "mixinextras",
      version = "0.5.4",
  ) {
      resolve(
          loaderArtifactOverrides(
              MinecraftModLoader.fabric to "mixinextras-fabric",
              MinecraftModLoader.forge to "mixinextras-forge",
              MinecraftModLoader.common to "mixinextras-common",
          )
      )
  }

  val MultiversionDependencies.klf: MultiversionDependencySpec by maven(
      group = "dev.nyon",
      artifact = "KotlinLangForge",
      version = "2.11.2-k2.3.21",
  ) {
      resolve { loader, mcVersion ->
          when (loader to mcVersion) {
              MinecraftModLoader.forge to MinecraftVersion.`20_1` ->
                  variant(version = "2.11.2-k2.3.21-2.0+forge")

              MinecraftModLoader.neoforge to MinecraftVersion.`21_1` ->
                  variant(version = "2.11.2-k2.3.21-3.0+neoforge")

              MinecraftModLoader.neoforge to MinecraftVersion.`26_1` ->
                  variant(version = "2.11.2-k2.3.21-3.1+neoforge")

              else -> error("No KLF variant for $loader / $mcVersion; choose a dependency manually")
          }
      }
  }
  ```

- [ ] **Step 2: Verify buildSrc compiles**

  Run: `./gradlew buildSrc:compileKotlin`

  Expected: BUILD SUCCESSFUL with no errors.

---

### Task 3: Update MultiversionDependencyPatterns.kt

**Files:**
- Modify: `buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt`

- [ ] **Step 1: Replace VariantOverride return type with DependencyVariant**

  Replace the entire file content with:

  ```kotlin
  import earth.terrarium.cloche.api.attributes.MinecraftModLoader

  fun loaderArtifactOverrides(vararg artifacts: Pair<MinecraftModLoader, String>): MultiversionResolver = { loader, _ ->
      artifacts.firstOrNull { it.first == loader }
          ?.let { DependencyVariant(artifact = it.second) }
          ?: DependencyVariant()
  }

  fun versionLoaderMcVersionPattern(version: String): MultiversionResolver = { loader, mcVersion ->
      DependencyVariant(version = "$version-${loader.name.lowercase()},${mcVersion.value}")
  }
  ```

- [ ] **Step 2: Verify buildSrc compiles**

  Run: `./gradlew buildSrc:compileKotlin`

  Expected: BUILD SUCCESSFUL with no errors.

---

### Task 4: Switch build.gradle.kts to use the project extension

**Files:**
- Modify: `build.gradle.kts`

- [ ] **Step 1: Replace the manual newInstance block with createMultiversionDependencies()**

  In `build.gradle.kts`, replace the manual instantiation block with:

  ```kotlin
  createMultiversionDependencies()
  ```

  All existing usages of `multiversionDependencies` then resolve through the project extension accessor.

- [ ] **Step 2: Verify the project configures without error**

  Run: `./gradlew help`

  Expected: BUILD SUCCESSFUL.
