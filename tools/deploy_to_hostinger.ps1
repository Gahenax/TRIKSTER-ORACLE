# Deploy TRICKSTER-ORACLE Frontend to Hostinger via FTP
# Usage: ./deploy_to_hostinger.ps1 -Password "your_ftp_password"

param (
    [Parameter(Mandatory=$true)]
    [string]$Password,
    [string]$HostIP = "212.1.209.105",
    [string]$User = "u314799704",
    [string]$RemoteDir = "public_html", # Adjust if deploying to a subdomain folder
    [string]$LocalDist = "frontend/dist"
)

$ErrorActionPreference = "Stop"

Write-Host "[*] Starting Hostinger FTP Deployment..." -ForegroundColor Cyan

if (-not (Test-Path $LocalDist)) {
    Write-Host "[!] local dist folder not found. Please run build first." -ForegroundColor Red
    exit 1
}

# Get all files in dist
$files = Get-ChildItem -Path $LocalDist -Recurse | Where-Object { -not $_.PSIsContainer }

Write-Host "[*] Uploading $($files.Count) files to ftp://$HostIP/$RemoteDir ..." -ForegroundColor Yellow

foreach ($file in $files) {
    $relativeName = $file.FullName.Replace((Get-Item $LocalDist).FullName + "\", "").Replace("\", "/")
    $remotePath = "ftp://$HostIP/$RemoteDir/$relativeName"
    
    Write-Host "[>] Uploading $relativeName ..." -ForegroundColor Gray
    
    # Use curl.exe for the upload
    # --ftp-create-dirs ensures subfolders (like assets/) are created
    & curl.exe --user "$($User):$($Password)" --ftp-create-dirs -T "$($file.FullName)" "$remotePath"
}

Write-Host "[OK] Deployment complete!" -ForegroundColor Green
