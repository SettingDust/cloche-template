# Build Script Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the template build logic into `buildSrc` while keeping explicit Cloche target declarations visible in the generated root build script.

**Architecture:** Add a generated `buildSrc` with precompiled convention plugins and Kotlin support sources under the `clocheTemplate` prefix. Move reusable support code and repeated defaults out of the root build script, but leave the target graph and `dependsOn` topology explicit in `build.gradle.kts.jinja`.

**Tech Stack:** Copier, Gradle Kotlin DSL, buildSrc precompiled script plugins, Cloche, Jinja templates

---

## File Structure

### Files to Create

- `buildSrc/build.gradle.kts`
- `buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja`
- `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`
- `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts`
- `buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja`
- `buildSrc/src/main/kotlin/ClocheTemplatePresets.kt`
- `buildSrc/src/main/kotlin/ContainerDsl.kt`
- `buildSrc/src/main/kotlin/CompatibilityRules.kt`
- `buildSrc/src/main/kotlin/VersionMappings.kt`

### Files to Modify

- `build.gradle.kts.jinja`
- `settings.gradle.kts.jinja`
- `copier.yml`
- `AGENTS.md`

### Validation Targets

- Generate a Kotlin project with bootstrap support enabled
- Generate a Java project with bootstrap support disabled
- Run `gradlew help` inside both generated projects

---

### Task 1: Add `buildSrc` generation skeleton

**Files:**
- Create: `buildSrc/build.gradle.kts`
- Modify: `copier.yml`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add generated `buildSrc` to the template layout**

Create `buildSrc/build.gradle.kts` with the plugin and dependency skeleton below.

```kotlin
plugins {
    `kotlin-dsl`
}

repositories {
    gradlePluginPortal()
    mavenCentral()
    maven("https://maven.msrandom.net/repository/cloche")
    maven("https://raw.githubusercontent.com/settingdust/maven/main/repository/") {
        name = "SettingDust's Maven"
    }
    mavenLocal()
}

kotlin {
    jvmToolchain(21)
}

dependencies {
    implementation("earth.terrarium.cloche:earth.terrarium.cloche.gradle.plugin:0.18.11-dust.17")
    implementation("com.gradleup.shadow:shadow-gradle-plugin:9.4.1")
    implementation("com.palantir.git-version:com.palantir.git-version.gradle.plugin:5.0.0")
    implementation("net.msrandom.minecraftcodev:net.msrandom.minecraftcodev.gradle.plugin:0.1.0")
    implementation(gradleApi())
}
```

- [ ] **Step 2: Keep repository-only planning artifacts out of generated projects**

Confirm `copier.yml` excludes `docs` and add `plans` to `_exclude` if it is not already present.

```yaml
_exclude:
  - "AGENTS.md"
  - "copier.yaml"
  - "copier.yml"
  - "~*"
  - ".git"
  - ".DS_Store"
  - "docs"
  - "plans"
  - "README.md"
  - ".idea"
```

- [ ] **Step 3: Document the new generated `buildSrc` in the agent guidance**

Update `AGENTS.md` in the generated project structure section so it mentions `buildSrc/` as part of the generated output.

```md
├── buildSrc/
│   ├── build.gradle.kts                 # build logic dependencies and precompiled plugins
│   └── src/main/kotlin/
│       ├── clocheTemplate.base.gradle.kts
│       ├── clocheTemplate.language.kotlin.gradle.kts
│       └── ...
```

- [ ] **Step 4: Validate the new skeleton renders cleanly**

Run: `copier copy . ..\cloche-template-smoke-buildsrc --unsafe --defaults`
Expected: success and a generated `buildSrc` directory in the destination.

- [ ] **Step 5: Commit the scaffold**

```bash
git add copier.yml AGENTS.md buildSrc/build.gradle.kts
git commit -m "build: add generated buildSrc scaffold"
```

### Task 2: Extract shared support code into Kotlin sources

**Files:**
- Create: `buildSrc/src/main/kotlin/ContainerDsl.kt`
- Create: `buildSrc/src/main/kotlin/CompatibilityRules.kt`
- Create: `buildSrc/src/main/kotlin/VersionMappings.kt`
- Modify: `build.gradle.kts.jinja`

- [ ] **Step 1: Move container DSL implementation into `ContainerDsl.kt`**

Create `buildSrc/src/main/kotlin/ContainerDsl.kt` and move the current root-script support code into an object-free Kotlin source file. Start the file with the imports and top-level declarations below.

```kotlin
@file:Suppress("UnstableApiUsage", "INVISIBLE_REFERENCE")

import com.github.jengelman.gradle.plugins.shadow.tasks.ShadowJar
import earth.terrarium.cloche.INCLUDE_TRANSFORMED_OUTPUT_ATTRIBUTE
import earth.terrarium.cloche.REMAPPED_ATTRIBUTE
import earth.terrarium.cloche.api.attributes.IncludeTransformationStateAttribute
import earth.terrarium.cloche.api.attributes.MinecraftModLoader
import earth.terrarium.cloche.api.attributes.RemapNamespaceAttribute
import earth.terrarium.cloche.api.attributes.TargetAttributes
import earth.terrarium.cloche.api.target.MinecraftTarget
import earth.terrarium.cloche.api.target.compilation.ClocheDependencyHandler
import earth.terrarium.cloche.util.fromJars
import groovy.lang.Closure
import net.msrandom.minecraftcodev.core.utils.lowerCamelCaseGradleName
import net.msrandom.minecraftcodev.fabric.task.JarInJar
import net.msrandom.minecraftcodev.forge.task.JarJar
import net.msrandom.minecraftcodev.includes.IncludesJar
import org.gradle.api.Action
import org.gradle.api.Project
import org.gradle.api.artifacts.Configuration
import org.gradle.api.artifacts.Dependency
import org.gradle.api.artifacts.ModuleDependency
import org.gradle.api.artifacts.type.ArtifactTypeDefinition
import org.gradle.api.attributes.AttributeContainer
import org.gradle.api.attributes.Category
import org.gradle.api.attributes.LibraryElements
import org.gradle.api.attributes.Usage
import org.gradle.api.file.CopySpec
import org.gradle.api.provider.Provider
import org.gradle.api.tasks.TaskProvider
import org.gradle.kotlin.dsl.named
import org.gradle.kotlin.dsl.register
import org.gradle.kotlin.dsl.support.serviceOf
```

Then move `ContainerScope`, `MinecraftModLoader.containerFeatureName()`, and `ClocheExtension.container(...)` out of `build.gradle.kts.jinja` into this file.

- [ ] **Step 2: Move compatibility rules into `CompatibilityRules.kt`**

Create the file with the extracted rules from the root script.

```kotlin
import earth.terrarium.cloche.api.attributes.MinecraftModLoader
import earth.terrarium.cloche.api.attributes.TargetAttributes
import org.gradle.api.attributes.AttributeCompatibilityRule
import org.gradle.api.attributes.CompatibilityCheckDetails

class MinecraftVersionCompatibilityRule : AttributeCompatibilityRule<String> {
    override fun execute(details: CompatibilityCheckDetails<String>) {
        details.compatible()
    }
}

class MinecraftModLoaderCompatibilityRule : AttributeCompatibilityRule<MinecraftModLoader> {
    override fun execute(details: CompatibilityCheckDetails<MinecraftModLoader>) {
        if (details.producerValue == MinecraftModLoader.common) {
            details.compatible()
        }
    }
}
```

- [ ] **Step 3: Move version and task-name helpers into `VersionMappings.kt`**

Create the file and move the current root-script extension functions and task-name helpers into it.

```kotlin
import earth.terrarium.cloche.api.target.FabricTarget
import earth.terrarium.cloche.api.target.ForgeLikeTarget
import earth.terrarium.cloche.api.target.ForgeTarget
import earth.terrarium.cloche.api.target.MinecraftTarget
import earth.terrarium.cloche.api.target.NeoforgeTarget
import net.msrandom.minecraftcodev.core.utils.lowerCamelCaseGradleName
import org.gradle.api.tasks.SourceSet

fun String.fabricApiVersion(): String? = when (this) {
    "1.20.1" -> "0.92.7"
    "1.21.1" -> "0.116.10"
    "26.1.2" -> "0.145.4"
    else -> null
}
```

Continue the file with the existing `parchmentVersion`, `forgeLoaderVersion`, `neoForgeLoaderVersion`, `isVersionTarget`, `disableVersionTemplateTasks`, and task-name extension properties.

- [ ] **Step 4: Delete the moved support code from `build.gradle.kts.jinja`**

Remove the extracted top-level classes and extension functions from the root script so the file stops owning reusable support code.

```kotlin
// Remove from the root script after extraction:
// - ContainerScope and related helpers
// - compatibility rule classes
// - version mapping and task-name helpers
```

- [ ] **Step 5: Validate the extracted support layer**

Run: `copier copy . ..\cloche-template-smoke-support --unsafe --defaults`
Expected: success and generated `buildSrc/src/main/kotlin` files in the destination.

- [ ] **Step 6: Commit the extraction**

```bash
git add build.gradle.kts.jinja buildSrc/src/main/kotlin/ContainerDsl.kt buildSrc/src/main/kotlin/CompatibilityRules.kt buildSrc/src/main/kotlin/VersionMappings.kt
git commit -m "refactor: extract build logic support sources"
```

### Task 3: Add convention plugins and metadata helper

**Files:**
- Create: `buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja`
- Create: `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`
- Create: `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts`
- Create: `buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja`
- Modify: `build.gradle.kts.jinja`

- [ ] **Step 1: Create the base convention plugin**

Create `buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja` with the shared plugin and repository setup that currently lives at the top of the root script.

```kotlin
plugins {
    java
    idea
    id("com.palantir.git-version")
    id("com.gradleup.shadow")
    id("earth.terrarium.cloche")
}

val archive_name: String by rootProject.properties
val source: String by rootProject.properties
val gitVersion: groovy.lang.Closure<String> by extra

base { archivesName = archive_name }
version = gitVersion()

repositories {
    exclusiveContent {
        forRepository {
            maven("https://api.modrinth.com/maven")
        }
        filter {
            includeGroup("maven.modrinth")
        }
    }

    maven("https://repo.nyon.dev/releases") {
        content {
            includeGroup("dev.nyon")
        }
    }

    mavenCentral()

    cloche {
        librariesMinecraft()
        main()
        mavenFabric()
        mavenForge()
        mavenNeoforged()
        mavenNeoforgedMeta()
        mavenParchment()
    }

    mavenLocal()
}
```

Then add back the remaining custom Maven blocks from the current root script.

- [ ] **Step 2: Create language convention plugins**

Create `buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts`.

```kotlin
plugins {
    kotlin("jvm") version "2.3.20"
    kotlin("plugin.serialization") version "2.3.20"
}
```

Create `buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts` as an intentionally empty marker plugin.

```kotlin
plugins {
}
```

- [ ] **Step 3: Add the metadata helper**

Create `buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja` with a helper that can be called inside `cloche {}`.

```kotlin
import earth.terrarium.cloche.ClocheExtension

fun ClocheExtension.clocheTemplateMetadata() {
    val id: String by project.rootProject.properties
    val source: String by project.rootProject.properties

    metadata {
        modId = id
        name = project.rootProject.property("name").toString()
        description = project.rootProject.property("description").toString()
        license = "{{ license }}"
        icon = "assets/$id/icon.png"
        sources = source
        issues = "$source/issues"
        author(project.rootProject.property("author").toString())
    }
}
```

- [ ] **Step 4: Replace root plugin and metadata boilerplate with helper usage**

Update `build.gradle.kts.jinja` so its plugin block becomes:

```kotlin
plugins {
    id("clocheTemplate.base")
    {%- if language == 'kotlin' %}
    id("clocheTemplate.language.kotlin")
    {%- else %}
    id("clocheTemplate.language.java")
    {%- endif %}
}
```

Then replace the long inline `metadata { ... }` block with a single helper call inside `cloche {}`.

```kotlin
cloche {
    clocheTemplateMetadata()
```

- [ ] **Step 5: Validate generated projects compile their build logic**

Run: `copier copy . ..\cloche-template-smoke-conventions --unsafe --defaults`
Run: `Push-Location ..\cloche-template-smoke-conventions; .\gradlew help; Pop-Location`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 6: Commit the convention layer**

```bash
git add build.gradle.kts.jinja buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts.jinja buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts buildSrc/src/main/kotlin/ClocheTemplateMetadata.kt.jinja
git commit -m "refactor: add clocheTemplate convention plugins"
```

### Task 4: Add target preset helpers and rename `game` / `service`

**Files:**
- Create: `buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja`
- Modify: `build.gradle.kts.jinja`
- Modify: `copier.yml`
- Modify: `AGENTS.md`

- [ ] **Step 1: Create target preset helpers**

Create `buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja` with focused extension helpers for existing targets.

```kotlin
import earth.terrarium.cloche.api.target.FabricTarget
import earth.terrarium.cloche.api.target.ForgeTarget
import earth.terrarium.cloche.api.target.MinecraftTarget
import earth.terrarium.cloche.api.target.NeoforgeTarget

fun MinecraftTarget.commonDefaults() {
}

fun MinecraftTarget.minecraftDefaults() {
}

fun ForgeTarget.bootstrapDefaults() {
}

fun FabricTarget.fabricDefaults() {
    loaderVersion = "0.19.2"
    includedClient()
}

fun ForgeTarget.forgeDefaults() {
    loaderVersion.set(minecraftVersion.map(String::forgeLoaderVersion))
}

fun NeoforgeTarget.neoforgeDefaults() {
    loaderVersion.set(minecraftVersion.map(String::neoForgeLoaderVersion))
}
```

Then migrate repeated loader-specific defaults from the root script into these helpers.

- [ ] **Step 2: Rename the template structure from `game` / `service` to `minecraft` / `bootstrap`**

Update `copier.yml` exclusion rules.

```yaml
_exclude:
  - "{% if not has_service %}src/forge/bootstrap{% endif %}"
  - "{% if not has_service %}src/neoforge/bootstrap{% endif %}"
  - "{% if not has_service %}src/minecraft{% endif %}"
```

Update `AGENTS.md` generated structure examples and terminology to use `minecraft` and `bootstrap`.

- [ ] **Step 3: Rename the root target declarations to the new terminology**

Update the root build script so the target names and variables move to `minecraft` and `bootstrap`.

```kotlin
    val minecraft = common("minecraft") {
        project.dependencies {
            // existing shared gameplay dependencies
        }
    }

    val minecraft201 = common("minecraft:20.1") {
        dependsOn(minecraft)
    }
```

And change the Forge and NeoForge bootstrap targets from `service` names to `bootstrap` names.

```kotlin
    val forgeBootstrap = forge("forge:bootstrap") {
        dependsOn(common201)
        minecraftVersion = "1.20.1"
    }
```

- [ ] **Step 4: Apply preset helpers in the root build script**

Replace repeated default blocks with helper calls, but keep explicit target creation and `dependsOn` visible.

```kotlin
    val fabric211 = fabric("fabric:21.1") {
        minecraftVersion = "1.21.1"
        fabricDefaults()
        dependsOn(common211, fabricCommon)
    }
```

- [ ] **Step 5: Validate Kotlin and Java output shapes**

Run: `copier copy . ..\cloche-template-kotlin-bootstrap --unsafe --defaults --data name=TestMod --data language=kotlin --data has_service=true`
Run: `copier copy . ..\cloche-template-java-no-bootstrap --unsafe --defaults --data name=TestMod --data language=java --data has_service=false`
Expected: both copies succeed, the Kotlin output contains `src/minecraft` and `src/forge/bootstrap`, and the Java output omits bootstrap folders.

- [ ] **Step 6: Commit the terminology and presets**

```bash
git add build.gradle.kts.jinja buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja copier.yml AGENTS.md
git commit -m "refactor: add target presets and rename phases"
```

### Task 5: Slim the root script and verify generated Gradle behavior

**Files:**
- Modify: `build.gradle.kts.jinja`
- Modify: `settings.gradle.kts.jinja`
- Test: generated smoke projects under `..\cloche-template-kotlin-bootstrap` and `..\cloche-template-java-no-bootstrap`

- [ ] **Step 1: Keep only orchestration logic in the root script**

Review `build.gradle.kts.jinja` and delete any remaining extracted support code or duplicated defaults so the file contains only:

```kotlin
plugins { ... }

cloche {
    clocheTemplateMetadata()

    // explicit target declarations
    // explicit dependsOn topology
    // project-specific target wiring
}
```

- [ ] **Step 2: Keep `settings.gradle.kts.jinja` focused on settings and catalog DSL**

Do not move the version-catalog helper DSL into `buildSrc` during this pass. Keep `settings.gradle.kts.jinja` as the owner of plugin management, dependency DSL, and version catalogs.

```kotlin
// keep in settings.gradle.kts.jinja
fun VersionCatalogBuilder.dependency(...)
fun VersionCatalogBuilder.modrinth(...)
```

- [ ] **Step 3: Run Gradle help in both generated smoke projects**

Run: `Push-Location ..\cloche-template-kotlin-bootstrap; .\gradlew help; Pop-Location`
Expected: `BUILD SUCCESSFUL`.

Run: `Push-Location ..\cloche-template-java-no-bootstrap; .\gradlew help; Pop-Location`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 4: Run a narrow template diff review**

Run: `git diff -- build.gradle.kts.jinja settings.gradle.kts.jinja copier.yml buildSrc AGENTS.md`
Expected: only the planned split, naming, and buildSrc additions appear.

- [ ] **Step 5: Commit the final root-script cleanup**

```bash
git add build.gradle.kts.jinja settings.gradle.kts.jinja copier.yml buildSrc AGENTS.md
git commit -m "refactor: slim root build script"
```

## Self-Review

### Spec coverage

- `clocheTemplate` prefix: covered in Tasks 3 and 4.
- Explicit target preservation: covered in Tasks 3 through 5.
- `buildSrc` capability layer: covered in Tasks 1 through 3.
- Metadata helper: covered in Task 3.
- `minecraft` / `bootstrap` rename: covered in Task 4.
- Root script slimming without matrix DSL: covered in Task 5.
- Copier exclusion of repository-only docs and plans: covered in Task 1.

### Placeholder scan

No `TODO`, `TBD`, or deferred implementation markers remain in the plan. Each task names exact files, commands, and code anchors.

### Type consistency

The plan consistently uses `clocheTemplate.base`, `clocheTemplate.language.kotlin`, `clocheTemplate.language.java`, `clocheTemplateMetadata()`, `minecraft`, and `bootstrap` across all tasks.
