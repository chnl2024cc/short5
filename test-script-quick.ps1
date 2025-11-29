# Quick test to verify the main script works
Write-Host "Testing test-browser.ps1 script..." -ForegroundColor Cyan
Write-Host ""

# Check if script exists
if (Test-Path ".\test-browser.ps1") {
    Write-Host "✓ Script file exists" -ForegroundColor Green
    
    # Check script syntax
    $errors = $null
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content ".\test-browser.ps1" -Raw), [ref]$errors)
    
    if ($errors.Count -eq 0) {
        Write-Host "✓ Script syntax is valid" -ForegroundColor Green
    } else {
        Write-Host "✗ Script has syntax errors:" -ForegroundColor Red
        $errors | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
    }
    
    # Check Docker
    try {
        $dockerVersion = docker --version 2>&1
        Write-Host "✓ Docker is available: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker is not available" -ForegroundColor Red
    }
    
    # Check docker compose
    try {
        $composeVersion = docker compose version 2>&1
        Write-Host "✓ Docker Compose is available: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker Compose is not available" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Ready to run: .\test-browser.ps1" -ForegroundColor Cyan
    Write-Host "Or with rebuild: .\test-browser.ps1 --rebuild" -ForegroundColor Cyan
} else {
    Write-Host "✗ Script file not found" -ForegroundColor Red
}
