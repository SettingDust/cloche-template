$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$requiredFiles = @(
    'buildSrc/src/main/kotlin/MinecraftVersions.kt',
    'buildSrc/src/main/kotlin/MultiversionDependencies.kt',
    'buildSrc/src/main/kotlin/MultiversionDependencyDelegates.kt',
    'buildSrc/src/main/kotlin/MultiversionDependencyResolution.kt',
    'buildSrc/src/main/kotlin/MultiversionDependencyPatterns.kt',
    'gradle/multiversion-dependencies.gradle.kts.jinja'
)

foreach ($relative in $requiredFiles) {
    if (-not (Test-Path (Join-Path $root $relative))) {
        throw "Missing required multiversion dependency file: $relative"
    }
}

$build = Get-Content (Join-Path $root 'build.gradle.kts.jinja') -Raw
$settings = Get-Content (Join-Path $root 'settings.gradle.kts.jinja') -Raw
$basePlugin = Get-Content (Join-Path $root 'buildSrc/src/main/kotlin/clocheTemplate.base.gradle.kts') -Raw

if ($build -notmatch 'import settingdust\.cloche_template\.buildsrc\.\*') {
    throw 'build.gradle.kts.jinja must import packaged buildSrc helpers'
}

if ($build -match 'apply\(from\s*=\s*"gradle/multiversion-dependencies\.gradle\.kts"\)') {
    throw 'build.gradle.kts.jinja must stop applying gradle/multiversion-dependencies.gradle.kts'
}

if ($basePlugin -notmatch 'createMultiversionDependencies\(\)') {
    throw 'clocheTemplate.base.gradle.kts must create the multiversionDependencies extension'
}

if ($build -notmatch 'multiversionDependencies\.mixinextras\.resolve\(this@forge, project\)') {
    throw 'build.gradle.kts.jinja must resolve mixinextras from the forge target context'
}

if ($build -notmatch 'multiversionDependencies\.klf\.resolve\(this@forge, project\)') {
    throw 'build.gradle.kts.jinja must resolve KLF from the forge target context'
}

if ($build -notmatch 'multiversionDependencies\.preloadingTricks\.resolve\(this@forge, project\)') {
    throw 'build.gradle.kts.jinja must resolve preloadingTricks from the forge target context'
}

if ($build -match 'catalog\.mixinextras|catalog\.klf') {
    throw 'build.gradle.kts.jinja must stop consuming catalog.mixinextras and catalog.klf'
}

if ($build -match 'catalog\.preloadingTricks') {
    throw 'build.gradle.kts.jinja must stop consuming catalog.preloadingTricks directly'
}

if ($settings -match 'dependency\("mixinextras"|dependency\("klf"') {
    throw 'settings.gradle.kts.jinja must stop declaring mixinextras and klf through the old multi-version catalog DSL'
}