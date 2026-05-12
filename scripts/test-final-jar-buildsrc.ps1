$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$buildFile = Join-Path $root 'build.gradle.kts.jinja'
$buildContent = Get-Content $buildFile -Raw
$helperFile = Join-Path $root 'buildSrc/src/main/kotlin/FinalJarDsl.kt.jinja'

if ($buildContent -match 'class\s+ForgeMetadataTransformer') {
    throw 'build.gradle.kts.jinja must not define ForgeMetadataTransformer directly.'
}

if ($buildContent -match 'shadowMergedDevJar|shadowMergedJar|shadowSourcesJar') {
    throw 'build.gradle.kts.jinja must not register final jar aggregation tasks directly.'
}

if ($buildContent -notmatch 'configureFinalJar\(') {
    throw 'build.gradle.kts.jinja must call configureFinalJar(...) from buildSrc.'
}

if (-not (Test-Path $helperFile)) {
    throw 'FinalJarDsl.kt.jinja must exist in buildSrc.'
}