$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    'buildSrc/src/main/kotlin/MinecraftVersions.kt.jinja',
    'buildSrc/src/main/kotlin/MultiversionDependencies.kt.jinja',
    'buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt.jinja',
    'buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt.jinja',
    'buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt.jinja',
    'gradle/multiversion-dependencies.gradle.kts.jinja'
)

foreach ($relative in $requiredFiles) {
    if (-not (Test-Path (Join-Path $root $relative))) {
        throw "Missing required multiversion dependency file: $relative"
    }
}

$build = Get-Content (Join-Path $root 'build.gradle.kts.jinja') -Raw
$settings = Get-Content (Join-Path $root 'settings.gradle.kts.jinja') -Raw

if ($build -notmatch 'apply\(from\s*=\s*"gradle/multiversion-dependencies.gradle.kts"\)') {
    throw 'build.gradle.kts.jinja must apply gradle/multiversion-dependencies.gradle.kts'
}

if ($build -match 'catalog\.mixinextras|catalog\.klf') {
    throw 'build.gradle.kts.jinja must stop consuming catalog.mixinextras and catalog.klf'
}

if ($settings -match 'dependency\("mixinextras"|dependency\("klf"') {
    throw 'settings.gradle.kts.jinja must stop declaring mixinextras and klf through the old multi-version catalog DSL'
}