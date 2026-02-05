# Quick Jules Status Check
# Una sola línea que puedes ejecutar desde PowerShell

cd C:\Users\USUARIO\.gemini\antigravity\playground\infinite-parsec\TRICKSTER-ORACLE; git fetch origin; $branch = git branch -r | Select-String "feature/phase1"; if ($branch) { Write-Host "`n✅ ¡JULES TRABAJANDO! Branch encontrado: $branch`n" -ForegroundColor Green; Write-Host "Commits recientes:" -ForegroundColor Yellow; git log origin/feature/phase1-monte-carlo-engine --oneline -5 2>$null; Write-Host "`nRevisa PRs en: https://github.com/Gahenax/TRIKSTER-ORACLE/pulls`n" -ForegroundColor Cyan } else { Write-Host "`n⏳ Jules NO ha comenzado. Branches actuales:" -ForegroundColor Yellow; git branch -r; Write-Host "`n" }
