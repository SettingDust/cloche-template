$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$conventionsFile = Join-Path $root 'buildSrc/src/main/kotlin/ClocheTemplatePresetConventions.kt.jinja'
$conventionsContent = Get-Content $conventionsFile -Raw
$presetFile = Join-Path $root 'buildSrc/src/main/kotlin/ClocheTemplatePresets.kt.jinja'
$content = Get-Content $presetFile -Raw
$buildFile = Join-Path $root 'build.gradle.kts.jinja'
$buildContent = Get-Content $buildFile -Raw
$kotlinPluginFile = Join-Path $root 'buildSrc/src/main/kotlin/clocheTemplate.language.kotlin.gradle.kts.jinja'
$kotlinPluginContent = Get-Content $kotlinPluginFile -Raw
$javaPluginFile = Join-Path $root 'buildSrc/src/main/kotlin/clocheTemplate.language.java.gradle.kts.jinja'
$javaPluginContent = Get-Content $javaPluginFile -Raw

if ($content -match '\{\{|-?%\}') {
    throw 'ClocheTemplatePresets.kt.jinja must not contain Jinja template syntax.'
}

if ($conventionsContent -match 'FabricMetadata|ForgeMetadata|fabricMetadata|forgeMetadata|neoforgeMetadata|applyFabricMetadata|applyForgeMetadata|applyNeoforgeMetadata') {
    throw 'ClocheTemplatePresetConventions must configure targets rather than metadata.'
}

if ($conventionsContent -notmatch 'FabricTarget\.\(\)\s*->\s*Unit') {
    throw 'ClocheTemplatePresetConventions must store FabricTarget configurators.'
}

if ($conventionsContent -notmatch 'ForgeTarget\.\(\)\s*->\s*Unit') {
    throw 'ClocheTemplatePresetConventions must store ForgeTarget configurators.'
}

if ($conventionsContent -notmatch 'NeoforgeTarget\.\(\)\s*->\s*Unit') {
    throw 'ClocheTemplatePresetConventions must store NeoforgeTarget configurators.'
}

if ($content -match 'applyFabricMetadata|applyForgeMetadata|applyNeoforgeMetadata') {
    throw 'ClocheTemplatePresets must apply target configurators instead of metadata configurators.'
}

if ($content -match 'fun\s+ForgeLikeTarget\.bootstrapDefaults\s*\(\s*project\s*:\s*Project\s*,\s*minecraftVersion\s*:') {
    throw 'bootstrapDefaults must not accept minecraftVersion.'
}

if ($content -match 'fun\s+FabricTarget\.fabricDefaults\s*\(\s*project\s*:\s*Project\s*,\s*configureMetadata\s*:') {
    throw 'fabricDefaults must not accept an inline configureMetadata callback.'
}

if ($content -match 'fun\s+ForgeTarget\.forgeDefaults\s*\(.*configureMetadata') {
    throw 'forgeDefaults must not accept an inline configureMetadata callback.'
}

if ($content -match 'fun\s+NeoforgeTarget\.neoforgeDefaults\s*\(.*configureMetadata') {
    throw 'neoforgeDefaults must not accept an inline configureMetadata callback.'
}

if ($buildContent -match 'fabricDefaults\(project\)[ \t]*\{') {
    throw 'build.gradle.kts.jinja must not pass inline metadata to fabricDefaults.'
}

if ($buildContent -match 'forgeDefaults\(\)') {
    throw 'build.gradle.kts.jinja should call forgeDefaults(project) so plugin-driven conventions can be resolved from the project.'
}

if ($buildContent -match 'neoforgeDefaults\(project\)[ \t]*\{') {
    throw 'build.gradle.kts.jinja must not pass inline metadata to neoforgeDefaults.'
}

if ($kotlinPluginContent -notmatch 'clocheTemplatePresetConventions') {
    throw 'Kotlin language plugin must register preset conventions.'
}

if ($javaPluginContent -notmatch 'clocheTemplatePresetConventions') {
    throw 'Java language plugin must register preset conventions.'
}