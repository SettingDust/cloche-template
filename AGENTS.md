# AGENTS.md

## Project Overview

This is a **Copier template** for generating multi-loader Minecraft mod projects. It automates the creation of well-structured Minecraft mods that support multiple loaders (Fabric, Forge, NeoForge) and multiple Minecraft versions (20.1, 21.1, 26.1).

### Key Features

- **Multi-loader support**: Generates Fabric, Forge, and NeoForge mod projects with shared code structures
- **Multi-version support**: Targets multiple Minecraft versions with version-specific source code separation
- **Language choice**: Supports both Kotlin and Java
- **Gradle-based**: Uses modern Gradle with version catalogs and Cloche build framework
- **Template-driven**: Jinja2 templates with dynamic project generation
- **Optional service layer**: Configurable Forge/NeoForge service-side code generation

### Tech Stack

- **Build System**: Gradle with Cloche plugin (custom multi-loader framework)
- **Template Engine**: Copier with Jinja2
- **Version Management**: Git-based versioning via `git-version` plugin
- **Packaging**: Shadow plugin for JAR shadowing/bundling
- **Mod Loaders**: Fabric, Forge, NeoForge
- **Languages**: Kotlin (v2.3.20) or Java
- **JVM Target**: Java version determined by build.gradle.kts.jinja and Minecraft version

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
| `has_service` | bool | Enable Forge/NeoForge service targets | `false` | true/false |
| `language` | str | Source code language | `kotlin` | `kotlin` or `java` |

### Post-Generation Tasks

After project generation, Copier automatically:
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

### Conditional Exclusion

The `_exclude` list in copier.yml controls which folders/files are pruned after rendering:

- **Language-based**: If language == `java`, all `**/main/kotlin` folders are excluded
- **Feature-based**: If has_service == `false`, `src/forge/service` and `src/neoforge/service` are excluded
- **Always excluded**: `copier.yml`, `README.md`, `.idea`, `.git`, `AI_CONTEXT.md`

### Important Template Variables in Generated Code

- `{{name}}`: Display name of the mod
- `{{id}}`: Snake-case unique identifier (used in filenames, mixins configs)
- `{{slug}}`: Kebab-case slug (used in URLs, archives)
- `{{group}}`: Maven group ID / Java package base (e.g., `com.example.mymod`)
- `{{author}}`: Author name
- `{{description}}`: Mod description
- `{{language}}`: `kotlin` or `java`
- `{{has_service}}`: boolean for service-side code generation
- `_copier_conf.sep`: Path separator (/ on Unix, \ on Windows)

## Generated Project Structure

After running `copier copy`, the generated project follows this structure:

```
{project}/
├── gradle/
│   └── wrapper/
│       └── gradle-wrapper.properties      # Gradle version specification
├── src/
│   ├── common/                            # Shared code across all loaders
│   │   ├── 20.1/main/                     # MC 1.20.1 specific
│   │   ├── 21.1/main/                     # MC 1.21 specific
│   │   ├── 26.1/main/                     # MC 1.26 specific
│   │   ├── common/main/                   # Version-agnostic shared code
│   │   └── game/                          # Game-only shared overlays
│   ├── fabric/common/main/                # Fabric-specific common code
│   ├── forge/
│   │   ├── game/main/                     # Forge game-side code
│   │   └── service/main/                  # Forge service-side code (if has_service=true)
│   ├── neoforge/
│   │   ├── game/main/                     # NeoForge game-side code
│   │   └── service/main/                  # NeoForge service-side code (if has_service=true)
│   └── game/                              # Cross-loader game layer
│       ├── 20.1/main/
│       ├── 21.1/main/
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

- **Cloche** (v0.18.11-dust.2): Multi-loader Minecraft modding framework
- **Shadow** (v9.4.1): JAR shadowing and bundling
- **Git-Version** (v5.0.0): Automated versioning from git history
- **Kotlin** (v2.3.20): Kotlin language support (if language == kotlin)

### Build Commands (Generated Project)

In any generated project, use these Gradle commands:

```bash
# Build the mod JAR
./gradlew build

# Build a specific loader (fabric, forge, neoforge, etc.)
./gradlew :fabric:build

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

1. **Update AI_CONTEXT.md**: Document changes to structure, variables, or build logic
2. **Modify .jinja files**: Only change rendered templates, not rendered output
3. **Update copier.yml**: If adding new questions, variables, or conditions
4. **Test generation**: Run `copier copy` locally to verify output is correct
5. **Validate Gradle**: Ensure generated `build.gradle.kts` is syntactically valid

### Common Template Modifications

#### Adding a New Minecraft Version

1. Create new versioned directories: `src/common/X.X/main/` and `src/game/X.X/main/`
2. Update README or copier.yml if version list is documented
3. Ensure gradle configuration auto-discovers new versions

#### Adding a New Loader

1. Create `src/{loader_name}/` folder structure
2. Update build.gradle.kts.jinja to add loader targets
3. Update Cloche configuration if needed
4. Add conditional exclusions to copier.yml if feature-gated

#### Adding Template Variables

1. Add to `copier.yml` with type, help text, defaults, and validator
2. Use `{{ variable_name }}` in `.jinja` files
3. Document the variable in this file and AI_CONTEXT.md

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
- **Game/Server split**: Use `game/` for game-side, `service/` for server-side (if has_service=true)

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

### Gradle Version Catalog

The template uses Gradle's version catalog feature for centralized dependency management. Check the generated `gradle/libs.versions.toml` or equivalent for:
- Plugin versions
- Dependency versions
- Platform-specific versions per Minecraft release

## Quick Navigation

Read files in this order for fastest orientation:

1. **AI_CONTEXT.md** — High-level repository contracts and what changes require documentation
2. **copier.yml** — Template questions, defaults, validators, and conditional logic
3. **README.md** — User-facing template documentation
4. **build.gradle.kts.jinja** — Build configuration and loader setup
5. **settings.gradle.kts.jinja** — Project structure and plugin repositories

## Contact & Documentation

- **Copier Docs**: https://copier.readthedocs.io/
- **AGENTS.md Format**: https://agents.md/
- **Cloche Documentation**: Check upstream Cloche project for multi-loader details
- **Minecraft Codedev**: https://github.com/msrandom/MinecraftCategoryDev
