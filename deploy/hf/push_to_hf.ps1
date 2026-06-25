# Deploy Echo Sense to Hugging Face Docker Space
# Usage: $env:HF_TOKEN = "hf_..." ; .\deploy\hf\push_to_hf.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$SpaceDir = Join-Path (Split-Path $Root -Parent) "echosense-ai-hf"
$SpaceRepo = "https://huggingface.co/spaces/Hamzavelous/echosense-ai"

if (-not $env:HF_TOKEN) {
    Write-Error "Set HF_TOKEN environment variable first."
}

function Sync-Tree {
    param([string]$Source, [string]$Dest, [string[]]$ExcludeDirs)
    if (Test-Path $Dest) { Remove-Item $Dest -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    $xd = @($ExcludeDirs | ForEach-Object { "/XD", $_ })
    & robocopy $Source $Dest /E /NFL /NDL /NJH /NJS /nc /ns /np @xd | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed for $Source" }
}

if (-not (Test-Path $SpaceDir)) {
    Write-Host "Cloning HF Space..."
    git clone "https://Hamzavelous:$($env:HF_TOKEN)@huggingface.co/spaces/Hamzavelous/echosense-ai" $SpaceDir
} else {
    Set-Location $SpaceDir
    git fetch origin
    git reset --hard origin/main 2>$null
    Set-Location $Root
}

Write-Host "Syncing deployment files (excluding node_modules, reports)..."

Sync-Tree (Join-Path $Root "backend") (Join-Path $SpaceDir "backend") @("reports", "data", "__pycache__", ".venv")
Sync-Tree (Join-Path $Root "frontend") (Join-Path $SpaceDir "frontend") @("node_modules", "dist")
# Echo_Logo.png omitted — HF git rejects binary files; PDF template falls back to text watermark

$deployDest = Join-Path $SpaceDir "deploy/hf"
New-Item -ItemType Directory -Force -Path $deployDest | Out-Null
Copy-Item (Join-Path $Root "deploy/hf/Dockerfile") (Join-Path $SpaceDir "Dockerfile") -Force
Copy-Item (Join-Path $Root "deploy/hf/requirements.txt") (Join-Path $SpaceDir "requirements.txt") -Force
Copy-Item (Join-Path $Root "deploy/hf/entrypoint.sh") (Join-Path $SpaceDir "entrypoint.sh") -Force
Copy-Item (Join-Path $Root "deploy/hf/README.md") (Join-Path $SpaceDir "README.md") -Force
Copy-Item (Join-Path $Root "deploy/hf/.dockerignore") (Join-Path $SpaceDir ".dockerignore") -Force
Copy-Item (Join-Path $Root "deploy/hf/gitignore") (Join-Path $SpaceDir ".gitignore") -Force
Copy-Item (Join-Path $Root "deploy/hf/*") $deployDest -Recurse -Force

Set-Location $SpaceDir
git add -A
git status --short | Select-Object -First 40
$changes = git status --porcelain
if (-not $changes) {
    Write-Host "No changes to deploy."
    exit 0
}
git commit -m "Deploy Echo Sense full-stack app to Docker Space" -m "React frontend + Flask API on port 7860 with SQLite and embedded ChromaDB."
git push "https://Hamzavelous:$($env:HF_TOKEN)@huggingface.co/spaces/Hamzavelous/echosense-ai" HEAD:main
if ($LASTEXITCODE -ne 0) { throw "git push failed (exit $LASTEXITCODE)" }

Write-Host "Deployed to $SpaceRepo"
