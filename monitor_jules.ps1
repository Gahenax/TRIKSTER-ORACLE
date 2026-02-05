# Monitor Jules Progress
# Ejecuta este script periódicamente para ver si Jules ha avanzado

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   TRICKSTER ORACLE - Jules Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$repoPath = "C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE"
Set-Location $repoPath

Write-Host "[1/4] Actualizando info del repositorio remoto..." -ForegroundColor Yellow
git fetch origin 2>&1 | Out-Null

Write-Host "[2/4] Verificando branches remotos..." -ForegroundColor Yellow
$branches = git branch -r
$julesBranch = $branches | Select-String "feature/phase1"

if ($julesBranch) {
    Write-Host "" 
    Write-Host "✅ ¡JULES HA CREADO UN BRANCH!" -ForegroundColor Green
    Write-Host "   Branch: $julesBranch" -ForegroundColor Green
    Write-Host ""
    
    # Mostrar commits de Jules
    Write-Host "[3/4] Commits de Jules:" -ForegroundColor Yellow
    git log origin/feature/phase1-monte-carlo-engine --oneline -10 2>$null
    
    Write-Host ""
    Write-Host "[4/4] Verificando Pull Requests..." -ForegroundColor Yellow
    Write-Host "   Revisa manualmente en:" -ForegroundColor Cyan
    Write-Host "   https://github.com/Gahenax/TRIKSTER-ORACLE/pulls" -ForegroundColor Cyan
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "   🎉 JULES ESTÁ TRABAJANDO!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    # Intentar abrir el navegador (opcional)
    $openBrowser = Read-Host "`n¿Abrir GitHub PRs en navegador? (s/n)"
    if ($openBrowser -eq "s") {
        Start-Process "https://github.com/Gahenax/TRIKSTER-ORACLE/pulls"
    }
    
} else {
    Write-Host "" 
    Write-Host "⏳ Jules NO ha comenzado todavía" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Posibles razones:" -ForegroundColor Gray
    Write-Host "  1. Aún no has creado el GitHub Issue" -ForegroundColor Gray
    Write-Host "  2. Jules está analizando las especificaciones" -ForegroundColor Gray
    Write-Host "  3. Jules comenzará en los próximos minutos/horas" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Branches actuales:" -ForegroundColor Yellow
    git branch -r
    Write-Host ""
    Write-Host "Último commit en master:" -ForegroundColor Yellow
    git log origin/master --oneline -1
}

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "Última verificación: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Enter para salir..."
Read-Host
