# AI Context: cloche-template

This file is the single source of truth for AI agents to understand this repository.
When the repository structure or generation logic changes, update this file in the same change.

## 1) Repository Purpose

- This repository is a Copier template for generating multi-loader Minecraft mod projects.
- It targets a Cloche-based build setup with shared and loader-specific source sets.
- Template rendering is driven by Jinja variables and Copier answers.

Primary entry points:
- README.md: user-facing usage notes (`copier copy`, `copier update`).
- copier.yml: template questions, defaults, validators, exclusion rules, and post-copy tasks.
- build.gradle.kts.jinja: main build logic template.
- settings.gradle.kts.jinja: plugin repos, version catalog DSL, project naming.
- gradle.properties.jinja: generated project properties.

## 2) Template and Rendering Model

- Files ending in `.jinja` are templates rendered by Copier.
- Dynamic paths and names use Jinja placeholders (for example: `{{id}}`, `{{ group.replace('.', _copier_conf.sep) }}`).
- `_exclude` in copier.yml controls conditional pruning (language-specific and service-specific folders).

Important Copier options (from copier.yml):
- name, id, slug, description, author, group, license
- has_service (whether forge/neoforge service targets are generated)
- language (`kotlin` or `java`)

## 3) Source Layout Strategy

Top-level `src/` is split by concern and platform:

- src/common/
  - `common/main`: shared logic/resources
  - `20.1/main`, `21.1/main`: MC-version-specific shared code/resources
  - `game/*`: game-only common overlays (versioned and unversioned)

- src/fabric/common/main
  - Fabric-specific common code/resources

- src/forge/
  - `game/main`: Forge game-side code/resources
  - `service/main`: optional service-side code/resources (gated by `has_service`)

- src/neoforge/
  - `game/main`: Neoforge game-side code/resources
  - `service/main`: optional service-side code/resources (gated by `has_service`)

- src/game/
  - Cross-loader game layer with version buckets (`20.1`, `21.1`, and shared `main`)

Language split in each source set:
- `main/java` and `main/kotlin` both exist in template form.
- Copier excludes one branch based on selected `language`.

## 4) Build/Dependency Design Notes

From build.gradle.kts.jinja and settings.gradle.kts.jinja:

- Build uses Cloche + Shadow + git-version plugins.
- Custom container packaging logic exists per mod loader (fabric/forge/neoforge).
- Version catalog includes a custom multi-version/multi-loader DSL.
- Repository definitions include central repos plus loader ecosystem repos.

If changing packaging, loader targets, or catalog DSL, update this file.

## 5) Rules for Future Changes

Always update this file when any of the following changes occur:

1. Any `src/` directory contract changes (add/remove/rename bucket, loader, or version folder).
2. Any new required template variable in copier.yml.
3. Any new template entry-point file that affects project generation.
4. Any significant build flow change in build.gradle.kts.jinja or settings.gradle.kts.jinja.
5. Any change to conditional exclusions in copier.yml `_exclude`.

## 6) Update Checklist (copy into PR description)

- [ ] Updated AI_CONTEXT.md for structure/design changes
- [ ] Verified directory map still matches real template paths
- [ ] Verified Copier variables list reflects copier.yml
- [ ] Verified build entry-point notes reflect current Gradle templates

## 7) Quick Navigation for AI Agents

Read files in this order for fastest orientation:

1. AI_CONTEXT.md
2. copier.yml
3. README.md
4. settings.gradle.kts.jinja
5. build.gradle.kts.jinja
6. src/ (only the folders relevant to the requested change)
