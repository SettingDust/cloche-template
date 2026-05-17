# AGENTS.md

## Project Overview

This is a **Copier template** for generating multi-loader Minecraft mod projects. It automates the creation of well-structured Minecraft mods that support multiple loaders (Fabric, Forge, NeoForge) and multiple Minecraft versions (20.1, 21.1, 26.1).

### Key Features

- **Multi-loader support**: Generates Fabric, Forge, and NeoForge mod projects with shared code structures
- **Multi-version support**: Targets multiple Minecraft versions with version-specific source code separation
- **Language choice**: Supports both Kotlin and Java
- **Gradle-based**: Uses modern Gradle, buildSrc convention plugins, and Cloche build framework
- **Template-driven**: Jinja2 templates with dynamic project generation
- **Optional bootstrap layer**: Configurable Forge/NeoForge bootstrap-side code generation

### Tech Stack

- **Build System**: Gradle with Cloche plugin (custom multi-loader framework)
- **Template Engine**: Copier with Jinja2
- **Version Management**: Git-based versioning via `git-version` plugin
- **Packaging**: Shadow plugin for JAR shadowing/bundling
- **Mod Loaders**: Fabric, Forge, NeoForge
- **Languages**: Kotlin (v2.3.20) or Java
- **JVM Target**: buildSrc uses JVM toolchain 25; generated mod targets are configured by the language convention plugins and Minecraft toolchains

## Using This Template

### Installation

1. Install Copier (Python-based):
   ```bash
   pip install copier
   ```

2. Generate a new Minecraft mod project:
   ```bash
   copier copy https://github.com/SettingDust/cloche-template path/to/destination
   ```

### Template Questions (Customization)

When running `copier copy`, you'll be prompted for:

| Variable | Type | Description | Default | Constraints |
|----------|------|-------------|---------|-------------|
| `name` | str | Mod name (display name) | (required) | Must start with letter, followed by alphanumeric chars |
| `id` | str | Unique mod identifier (snake_case) | `{{ name \| to_snake }}` | Must start with letter, followed by alphanumeric/underscore |
| `slug` | str | URL slug (kebab-case) | `{{ name \| to_kebab }}` | Must start with letter, followed by alphanumeric/dash |
| `description` | str | Short mod description | `{{ name }}` | (optional) |
| `author` | str | Author name | `SettingDust` | (any string) |
| `group` | str | Maven group ID (Java package) | `{{ author \| lower }}.{{ id }}` | Must start with letter, followed by alphanumeric/underscore/dot |
| `license` | str | License type | `Apache License 2.0` | (any string) |
| `has_service` | bool | Enable Forge/NeoForge bootstrap targets | `false` | true/false |
| `language` | str | Source code language | `kotlin` | `kotlin` or `java` |

### Post-Generation Tasks

After project generation, Copier automatically:
1. Runs `.copier/tasks/post_gen.py` to migrate/remove feature- and language-specific template files
1. Initializes a git repository (`git init`)
2. Stages all files (`git add .`)
3. Makes gradlew executable (`git update-index --chmod=+x ./gradlew`)

### Updating Generated Projects

To update an existing project to the latest template version:

```bash
cd path/to/generated/project
copier update
```

## Templating and Dynamic Generation

### Jinja2 Template Syntax

Files ending in `.jinja` are processed by Copier during generation. Common template patterns:

- **Variable substitution**: `{{variable_name}}` → replaced with user input or default
- **Path transformation**: `{{ group.replace('.', _copier_conf.sep) }}` → converts dot-notation package names to filesystem paths
- **Conditionals**: `{% if condition %}content{% endif %}`
- **Filters**: `| to_snake`, `| to_kebab`, `| lower`

### Conditional Exclusion and Post-Generation Cleanup

The `_exclude` list in copier.yml removes template-only files and folders before rendering output:

- **Always excluded**: `AGENTS.md`, `copier.yml`, `copier.yaml`, `scripts/*`, `docs`, `README.md`, `.idea`, `.git`, `.DS_Store`, `~*`

The generated `.copier/tasks/post_gen.py` then performs dynamic cleanup:

- **Language-based**: If `language == java`, remove generated `src/**/main/kotlin` mod sources. If `language == kotlin`, remove generated Java mod sources according to `has_service`.
- **Bootstrap language**: Bootstrap targets are Java-only; `src/*/bootstrap/**/main/kotlin` is always removed.
- **Feature-based**: If `has_service == false`, remove `src/forge/bootstrap`, `src/neoforge/bootstrap`, and `src/minecraft`.
- **Service split**: If `has_service == true`, move versioned `IdentifierFactory` and `MinecraftAdapter` implementations from `src/common/{version}` to `src/minecraft/{version}` and remove minecraft-side `LoaderAdapter` files for Forge/NeoForge.

### Important Template Variables in Generated Code

- `{{name}}`: Display name of the mod
- `{{id}}`: Snake-case unique identifier (used in filenames, mixins configs)
- `{{slug}}`: Kebab-case slug (used in URLs, archives)
- `{{group}}`: Maven group ID / Java package base (e.g., `com.example.mymod`)
- `{{author}}`: Author name
- `{{description}}`: Mod description
- `{{language}}`: `kotlin` or `java`
- `{{has_service}}`: boolean for bootstrap-side code generation
- `_copier_conf.sep`: Path separator (/ on Unix, \ on Windows)

## Generated Project Structure

After running `copier copy`, the generated project follows this structure:

```
{project}/
├── buildSrc/
│   ├── build.gradle.kts                    # build logic dependencies and precompiled plugins
│   └── src/
│       └── main/
│           └── kotlin/                    # extracted build logic helpers and convention plugins
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties      # Gradle version specification
├── src/
│   ├── common/                            # Shared code across all loaders
│   │   ├── 20.1/main/                     # MC 1.20.1 specific
│   │   ├── 21.1/main/                     # MC 1.21 specific
│   │   ├── 26.1/main/                     # MC 1.26 specific
│   │   └── common/main/                   # Version-agnostic shared code
│   ├── fabric/common/main/                # Fabric-specific common code
│   ├── forge/
│   │   ├── minecraft/main/                # Forge minecraft-side code
│   │   └── bootstrap/main/                # Forge bootstrap-side code (if has_service=true)
│   ├── neoforge/
│   │   ├── minecraft/common/main/         # NeoForge common minecraft-side code
│   │   ├── minecraft/21.1/main/           # NeoForge MC 1.21-specific code
│   │   ├── minecraft/26.1/main/           # NeoForge MC 1.26-specific code
│   │   └── bootstrap/common|21.1|26.1/    # NeoForge bootstrap code (if has_service=true)
│   └── minecraft/                         # Cross-loader minecraft layer (if has_service=true)
│       ├── 21.1/main/
│       ├── 26.1/main/
│       └── main/
├── build.gradle.kts                       # Main build file (rendered from template)
├── settings.gradle.kts                    # Settings and project layout (rendered from template)
├── gradle.properties                      # Gradle properties (rendered from template)
├── gradlew / gradlew.bat                  # Gradle wrapper scripts
└── README.md                              # Project-specific readme (generated)
```

Each source folder contains:
- `main/java/` → Java source code
- `main/kotlin/` → Kotlin source code (only one language kept based on `language` variable)
- `main/resources/` → Resources, configs, mixins, etc.

## Build System

### Gradle Plugins Used

- **Cloche** (v0.18.11-dust.18): Multi-loader Minecraft modding framework
- **Shadow** (v9.4.1): JAR shadowing and bundling
- **Git-Version** (v5.0.0): Automated versioning from git history
- **Kotlin** (v2.3.20): Kotlin language support (if language == kotlin)

### Build Commands (Generated Project)

In any generated project, use these Gradle commands:

```bash
# Build the mod JAR
./gradlew build

# Run Minecraft in development environment
./gradlew runClient

# Run server side
./gradlew runServer

# Remapped JAR (for IDE classpath, deobfuscated)
./gradlew remapJar

# Generate IDE run configurations
./gradlew genSources

# Clean build artifacts
./gradlew clean
```

### Gradle Properties

These are automatically set from template variables:

```properties
archive_name={{slug}}           # Output JAR name prefix
id={{id}}                       # Mod ID
name={{name}}                   # Display name
author={{author}}               # Author
description={{description}}     # Description
source=https://github.com/...   # Source URL (if GitHub)
```

## Development Workflow (For Agents Working on This Template)

### Understanding Template Rendering

1. Copier reads `copier.yml` for configuration and questions
2. User answers template questions
3. Copier processes all `.jinja` files with Jinja2 engine
4. Conditional exclusions are applied based on feature flags
5. Generated project is created in the destination folder

### Making Changes to This Template

When modifying the template itself:

1. **Modify templates and buildSrc sources intentionally**: `.jinja` files are rendered by Copier; static buildSrc `.kt`/`.gradle.kts` files are copied directly.
2. **Update copier.yml**: If adding new questions, variables, excludes, or tasks.
3. **Update `.copier/tasks/post_gen.py.jinja`**: If feature/language cleanup or source migration rules change.
4. **Run targeted scripts**: Use scripts under `scripts/` for structural smoke checks where relevant.
5. **Test generation**: Run `copier copy` locally to verify output is correct.
6. **Validate Gradle**: Ensure generated `build.gradle.kts` and buildSrc compile.

### Common Template Modifications

#### Adding a New Minecraft Version

1. Create new versioned directories under `src/common/X.X/main/`, `src/minecraft/X.X/main/`, and loader-specific folders as needed.
2. Update `build.gradle.kts.jinja` target/container/run configuration.
3. Update buildSrc version helpers such as `MinecraftVersions.kt`, `VersionMappings.kt`, and multiversion dependency rules when needed.
4. Update `.copier/tasks/post_gen.py.jinja` migration/removal maps if versioned files move during generation.
5. Update docs if the supported version list changes.

#### Adding a New Loader

1. Create `src/{loader_name}/` folder structure
2. Update build.gradle.kts.jinja to add loader targets
3. Update Cloche configuration if needed
4. Add conditional exclusions to copier.yml if feature-gated

#### Adding Template Variables

1. Add to `copier.yml` with type, help text, defaults, and validator
2. Use `{{ variable_name }}` in `.jinja` files
3. Document the variable in this file if it affects generated structure or workflow

## Testing Instructions

### Validating Template Generation

```bash
# Generate test project from template
copier copy . /tmp/test_mod

# Verify generated structure
ls -R /tmp/test_mod/src/

# Test Gradle build in generated project
cd /tmp/test_mod
./gradlew build

# Verify JAR was created
ls build/libs/
```

### Template Validation Steps

1. **Verify Jinja rendering**: No `{{ }}` placeholders remain in generated files
2. **Check conditionals**: Confirm unused code branches are excluded
3. **Validate Gradle syntax**: Generated `build.gradle.kts` must be valid Kotlin DSL
4. **Test project generation**: Run template with all combinations of boolean options
5. **Language verification**: If language=java, no kotlin files; if language=kotlin, no java files

### Sanity Checks for Template Changes

Before committing template changes:

```bash
# Test with Kotlin, all features, multiple versions
copier copy . /tmp/test_kotlin_full \
  --data name=TestMod \
  --data language=kotlin \
  --data has_service=true

# Test with Java, minimal features
copier copy . /tmp/test_java_min \
  --data name=TestMod \
  --data language=java \
  --data has_service=false

# Verify both generated projects build
cd /tmp/test_kotlin_full && ./gradlew build
cd /tmp/test_java_min && ./gradlew build

# Run template contract checks from the template repository
python ./scripts/test_template_contract.py
python ./scripts/test_packaging_contract.py
python ./scripts/test_multiversion_contract.py
python ./scripts/test_template_generation.py

# Optional slow generated-project builds
$env:CLOCHE_RUN_SLOW_TESTS=1; python ./scripts/test_generated_builds.py
```

## Code Style and Conventions

### Jinja Template Style

- **Use snake_case** for variable names: `{{my_variable}}`
- **Indent Jinja blocks**: Use proper indentation to match generated code structure
- **Document complex logic**: Add comments explaining conditional logic
- **Filter usage**: Use built-in Copier filters (`to_snake`, `to_kebab`, `lower`) for name transformations

### Kotlin Code Style (Generated Projects)

- **Official Kotlin style**: Enforced via `kotlin.code.style=official` in gradle.properties
- **Serialization support**: Built-in via `kotlin("plugin.serialization")`
- **Package naming**: Based on `{{group}}` variable (e.g., `com.author.modid`)

### Java Code Style (Generated Projects)

- Java 17+ (minimum, typically higher for newer MC versions)
- Package naming follows `{{group}}` convention
- UTF-8 encoding enforced: `systemProp.file.encoding=utf-8`

### File Organization (Generated Projects)

- **Shared code**: `src/common/` (loader-independent, all versions)
- **Version-specific shared**: `src/common/{version}/` (MC-version-specific, all loaders)
- **Loader-specific**: `src/{loader}/` (all versions, loader-specific)
- **Minecraft/Bootstrap split**: Use `minecraft/` for runtime-side code, `bootstrap/` for pre-launch loader-side code (if has_service=true). Bootstrap code is Java-only.
- **Generated cleanup matters**: Inspect `.copier/tasks/post_gen.py.jinja` before changing source layout; it moves/removes files after Copier renders templates.

## Important Concepts for Agents

### Cloche Build Framework

Cloche is a custom multi-loader modding framework that:
- Manages shared code between loaders (common source sets)
- Handles loader-specific compilation and packaging
- Provides unified build targets across Fabric/Forge/NeoForge
- Uses Minecraft Codedev for deobfuscation and remapping

### Mixin Configuration

- Mixins configs are generated per version and loader
- Files like `{{id}}.mixins.json.jinja` are rendered during template generation
- Mixin access wideners are defined in `{{id}}.accessWidener`

### JAR Artifacts

- Shadow plugin packages dependencies into JARs
- Each loader produces platform-specific JARs
- Git-version plugin auto-increments versions from git tags

### BuildSrc Conventions and Dependency Helpers

The template centralizes build logic in buildSrc:

- `clocheTemplate.base.gradle.kts` configures shared plugins and project defaults.
- `clocheTemplate.language.kotlin.gradle.kts` and `clocheTemplate.language.java.gradle.kts` configure language-specific behavior.
- `MultiversionDependencies*`, `MinecraftVersions`, and `VersionMappings` support loader/version-specific dependency resolution.
- `MultiversionDependencies*`, `MinecraftVersions`, and `VersionMappings` declare generated-project dependency variants such as MixinExtras and KotlinLangForge.

## Quick Navigation

Read files in this order for fastest orientation:

1. **AGENTS.md** — Repository overview and workflow notes
2. **copier.yml** — Template questions, defaults, validators, excludes, and tasks
3. **.copier/tasks/post_gen.py.jinja** — Post-generation cleanup and source migration
4. **buildSrc/build.gradle.kts** — Build logic dependencies and toolchain
5. **buildSrc/src/main/kotlin/** — Convention plugins and helper DSLs
6. **build.gradle.kts.jinja** — Generated build configuration and loader setup
7. **buildSrc/src/main/kotlin/MultiversionDependencies.kt** — Multiversion dependency extension
8. **buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt** — Generated-project dependency presets
9. **settings.gradle.kts.jinja** — Project settings and plugin repositories

## Contact & Documentation

- **Copier Docs**: https://copier.readthedocs.io/
- **AGENTS.md Format**: https://agents.md/
- **Cloche Documentation**: Check upstream Cloche project for multi-loader details
- **Minecraft Codedev**: https://github.com/msrandom/MinecraftCategoryDev
