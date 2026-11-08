param(
    [string]$SkillsRoot,
    [string]$Python = 'python',
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$backupPackage = $null

function Assert-DirectoryAncestors([string]$Path) {
    $checked = $Path
    while ($checked) {
        # Get-Item -Force sees hidden entries and reparse points, including dangling links.
        $item = Get-Item -LiteralPath $checked -Force -ErrorAction SilentlyContinue
        if ($null -ne $item) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Linked/reparse path refused: $checked"
            }
            if (-not $item.PSIsContainer) { throw "File/directory conflict: $checked" }
        }
        $checked = Split-Path -Path $checked -Parent
    }
}

function Test-Within([string]$Path, [string]$Parent) {
    return $Path.Equals($Parent, [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($Parent.TrimEnd([IO.Path]::DirectorySeparatorChar) +
            [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)
}

function Assert-NoOverlap([string]$First, [string]$Second) {
    if ((Test-Within $First $Second) -or (Test-Within $Second $First)) {
        throw "Overlapping paths refused: $First; $Second"
    }
}

function Read-TargetTree([string]$Directory, [string]$Prefix = '') {
    foreach ($item in Get-ChildItem -LiteralPath $Directory -Force) {
        $relative = if ($Prefix) { $Prefix + '/' + $item.Name } else { $item.Name }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            throw "Linked/reparse target entry refused: $relative"
        }
        $isCacheDirectory = $item.PSIsContainer -and $item.Name -ceq '__pycache__' -and
            $expectedDirectories.ContainsKey($Prefix)
        $isCacheFile = -not $item.PSIsContainer -and
            ($Prefix -ceq '__pycache__' -or $Prefix.EndsWith('/__pycache__')) -and
            $item.Extension -ceq '.pyc'
        if ($item.PSIsContainer) {
            if (-not $expectedDirectories.ContainsKey($relative) -and -not $isCacheDirectory) {
                throw "Unexpected target directory or file/directory conflict: $relative"
            }
            Read-TargetTree $item.FullName $relative
        } else {
            if (-not $expectedFiles.ContainsKey($relative) -and -not $isCacheFile) {
                throw "Unexpected target file or file/directory conflict: $relative"
            }
            [pscustomobject]@{ path = $relative; sha256 =
                (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant() }
        }
    }
}

function Assert-Hashes([string]$Directory, $Files) {
    foreach ($entry in $Files) {
        $file = Join-Path $Directory $entry.path
        $item = Get-Item -LiteralPath $file -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Copied file conflict/link: $($entry.path)"
        }
        $hash = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($hash -cne $entry.sha256) { throw "Hash verification failed: $($entry.path)" }
    }
}

try {
    $source = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../skills/skill-publishing-guide'))
    $checker = Join-Path $PSScriptRoot 'check_skill.py'
    $sourceJson = & $Python $checker $source --json
    if ($LASTEXITCODE -ne 0) { throw 'Source validation failed; target unchanged' }
    $manifest = ($sourceJson -join "`n") | ConvertFrom-Json
    if ($manifest.name -cne 'skill-publishing-guide') { throw 'Unexpected skill name' }
    if (-not $SkillsRoot) {
        if (-not $env:USERPROFILE) { throw 'USERPROFILE is required for the default SkillsRoot' }
        $SkillsRoot = Join-Path $env:USERPROFILE '.agents/skills'
    }
    $skillsParent = [IO.Path]::GetFullPath($SkillsRoot)
    $target = [IO.Path]::GetFullPath((Join-Path $skillsParent $manifest.name))
    Assert-NoOverlap $source $target
    Assert-DirectoryAncestors $source
    Assert-DirectoryAncestors $target
    $expectedFiles = @{}
    $expectedDirectories = @{ '' = $true }
    foreach ($entry in $manifest.files) {
        $expectedFiles[$entry.path] = $entry.sha256
        $directory = $entry.path
        while ($directory.Contains('/')) {
            $directory = $directory.Substring(0, $directory.LastIndexOf('/'))
            $expectedDirectories[$directory] = $true
        }
    }
    $targetExists = Test-Path -LiteralPath $target -PathType Container
    $oldFiles = if ($targetExists) { @(Read-TargetTree $target) } else { @() }
    $oldHashes = @{}
    foreach ($entry in $oldFiles) { $oldHashes[$entry.path] = $entry.sha256 }
    $changes = @($manifest.files | Where-Object { $oldHashes[$_.path] -cne $_.sha256 }).Count
    Write-Output "Source: $source"
    Write-Output "Target: $target"
    Write-Output "Version: $($manifest.version)"
    Write-Output "Changes: $changes"
    if ($changes -eq 0) {
        Write-Output 'PASS: Already current; no writes'
        exit 0
    }
    if ($targetExists) {
        if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is required for update backups' }
        $backupRoot = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'SkillBackups/skill-publishing-guide'))
        Assert-NoOverlap $backupRoot $source
        Assert-NoOverlap $backupRoot $target
        Assert-DirectoryAncestors $backupRoot
        $backupRun = Join-Path $backupRoot ((Get-Date -Format 'yyyyMMdd-HHmmssfff') + '-' + [Guid]::NewGuid().ToString('N'))
        $backupPackage = [IO.Path]::GetFullPath((Join-Path $backupRun $manifest.name))
        Assert-NoOverlap $backupPackage $source
        Assert-NoOverlap $backupPackage $target
        Assert-DirectoryAncestors $backupPackage
        if (Test-Path -LiteralPath $backupRun) { throw 'Unique backup path already exists' }
    }
    if ($DryRun) {
        Write-Output 'PASS: DryRun; no writes'
        exit 0
    }
    # A changed source must still match the original manifest before any backup/write.
    Assert-Hashes $source $manifest.files
    if ($targetExists) {
        New-Item -ItemType Directory -Path $backupRun | Out-Null
        Copy-Item -LiteralPath $target -Destination $backupPackage -Recurse -Force
        Assert-Hashes $backupPackage $oldFiles
        Write-Output "Backup: $backupPackage"
    }
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    foreach ($entry in $manifest.files) {
        $destination = Join-Path $target $entry.path
        New-Item -ItemType Directory -Path (Split-Path -Path $destination -Parent) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $source $entry.path) -Destination $destination -Force
    }
    Assert-DirectoryAncestors $target
    $null = @(Read-TargetTree $target)
    Assert-Hashes $target $manifest.files
    Write-Output "PASS: Installed $($manifest.name) $($manifest.version)"
    exit 0
} catch {
    if ($backupPackage) { Write-Warning "Install failed. Inspect retained backup if present: $backupPackage" }
    Write-Error $_ -ErrorAction Continue
    exit 1
}
