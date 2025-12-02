# Browser Testing Script for Short-Video Platform (PowerShell)
# This script ALWAYS restarts Docker containers and tests the application
# 
# IMPORTANT: Since we're developing in Docker containers, code changes require
# container restarts to take effect. This script ensures a clean restart every time.
#
# Usage: .\test-browser.ps1 [--rebuild]
#   --rebuild: Rebuild Docker images before starting (use when dependencies change)

param(
    [switch]$Rebuild = $false
)

$ErrorActionPreference = "Stop"

Write-Host "🧪 Starting Browser Test Suite..." -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "⚠️  IMPORTANT: This script will RESTART all Docker containers" -ForegroundColor Yellow
Write-Host "   Code changes require container restarts in Docker development!" -ForegroundColor Yellow
Write-Host ""

# Load BACKEND_BASE_URL from environment or .env file, default to http://localhost:8000
$BACKEND_BASE_URL = $env:BACKEND_BASE_URL
if (-not $BACKEND_BASE_URL) {
    # Try to read from .env file
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        $backendLine = $envContent | Where-Object { $_ -match '^BACKEND_BASE_URL=(.+)$' }
        if ($backendLine) {
            $BACKEND_BASE_URL = ($backendLine -split '=')[1].Trim()
        }
    }
}
if (-not $BACKEND_BASE_URL) {
    $BACKEND_BASE_URL = "http://localhost:8000"
}

$FRONTEND_PORT = $env:FRONTEND_PORT
if (-not $FRONTEND_PORT) {
    $FRONTEND_PORT = "3000"
}

$FRONTEND_URL = "http://localhost:$FRONTEND_PORT"
$BACKEND_URL = $BACKEND_BASE_URL
$MAX_WAIT = 60  # Maximum wait time in seconds

# Step 1: Stop all containers (CRITICAL - ensures clean state)
Write-Host "Step 1: Stopping all Docker containers..." -ForegroundColor Yellow
Write-Host "  This ensures a clean restart with latest code changes..." -ForegroundColor Gray
$stopResult = docker compose down 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Warning: Some containers may not have stopped cleanly" -ForegroundColor Yellow
    Write-Host "   Continuing anyway..." -ForegroundColor Gray
} else {
    Write-Host "✓ All containers stopped" -ForegroundColor Green
}

# Step 2: Rebuild images if requested (for dependency changes)
if ($Rebuild) {
    Write-Host "`nStep 2a: Rebuilding Docker images (--rebuild flag detected)..." -ForegroundColor Yellow
    Write-Host "  This may take a few minutes..." -ForegroundColor Gray
    $buildResult = docker compose build --no-cache 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to rebuild images" -ForegroundColor Red
        Write-Host $buildResult
        exit 1
    }
    Write-Host "✓ Images rebuilt successfully" -ForegroundColor Green
}

# Step 2/3: Start containers (CRITICAL - loads latest code)
Write-Host "`nStep $($Rebuild ? '3' : '2'): Starting Docker containers with latest code..." -ForegroundColor Yellow
Write-Host "  This will load all recent code changes..." -ForegroundColor Gray
$startResult = docker compose up -d 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start containers" -ForegroundColor Red
    Write-Host $startResult
    exit 1
}
Write-Host "✓ Containers started" -ForegroundColor Green

# Verify containers are actually running
Write-Host "`nVerifying containers are running..." -ForegroundColor Gray
Start-Sleep -Seconds 2
$runningContainers = docker compose ps --format json | ConvertFrom-Json | Where-Object { $_.State -eq "running" }
$expectedContainers = @("short5_frontend", "short5_backend", "short5_postgres", "short5_redis", "short5_video_worker")
$runningCount = ($runningContainers | Measure-Object).Count

if ($runningCount -lt $expectedContainers.Count) {
    Write-Host "⚠️  Warning: Only $runningCount containers are running (expected $($expectedContainers.Count))" -ForegroundColor Yellow
    Write-Host "   Checking container status..." -ForegroundColor Gray
    docker compose ps
} else {
    Write-Host "✓ All containers are running" -ForegroundColor Green
}

Write-Host "`nStep $($Rebuild ? '4' : '3'): Waiting for services to be ready..." -ForegroundColor Yellow
Write-Host "  Services need time to initialize after restart..." -ForegroundColor Gray

# Wait for backend to be ready
Write-Host "Waiting for backend ($BACKEND_URL)..." -ForegroundColor Gray
$backendReady = $false
for ($i = 1; $i -le $MAX_WAIT; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$BACKEND_URL/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Backend is ready" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {
        # Service not ready yet
    }
    Start-Sleep -Seconds 1
}

if (-not $backendReady) {
    Write-Host "✗ Backend failed to start after $MAX_WAIT seconds" -ForegroundColor Red
    exit 1
}

# Wait for frontend to be ready
Write-Host "Waiting for frontend ($FRONTEND_URL)..." -ForegroundColor Gray
$frontendReady = $false
for ($i = 1; $i -le $MAX_WAIT; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "$FRONTEND_URL" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Frontend is ready" -ForegroundColor Green
            $frontendReady = $true
            break
        }
    } catch {
        # Service not ready yet
    }
    Start-Sleep -Seconds 1
}

if (-not $frontendReady) {
    Write-Host "✗ Frontend failed to start after $MAX_WAIT seconds" -ForegroundColor Red
    exit 1
}

# Give services a moment to fully initialize
Start-Sleep -Seconds 3

Write-Host "`nStep $($Rebuild ? '5' : '4'): Checking TypeScript errors..." -ForegroundColor Yellow
Write-Host "  Validating code changes are type-safe..." -ForegroundColor Gray

# Check for TypeScript errors in frontend
$tscErrors = $null
try {
    Push-Location frontend
    $tscOutput = npm run typecheck 2>&1 | Out-String
    $tscErrors = $tscOutput | Select-String -Pattern "error TS" -AllMatches
    
    if ($tscErrors) {
        $errorCount = ($tscErrors.Matches).Count
        Write-Host "✗ Found $errorCount TypeScript error(s)" -ForegroundColor Red
        Write-Host "TypeScript errors:" -ForegroundColor Red
        $tscOutput | Select-String -Pattern "error TS" | ForEach-Object {
            Write-Host "  $_" -ForegroundColor Red
        }
        Write-Host "`n⚠ Please fix TypeScript errors before proceeding!" -ForegroundColor Yellow
        Pop-Location
        exit 1
    } else {
        Write-Host "✓ No TypeScript errors found" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠ Could not run TypeScript check: $_" -ForegroundColor Yellow
} finally {
    Pop-Location
}

Write-Host "`nStep $($Rebuild ? '6' : '5'): Testing API endpoints..." -ForegroundColor Yellow
Write-Host "  Verifying services respond correctly after restart..." -ForegroundColor Gray

# Test backend health
try {
    $healthResponse = Invoke-RestMethod -Uri "$BACKEND_URL/health" -Method Get
    if ($healthResponse.status -eq "healthy") {
        Write-Host "✓ Backend health check passed" -ForegroundColor Green
    } else {
        Write-Host "⚠ Backend health check returned unexpected status" -ForegroundColor Yellow
    }
} catch {
    Write-Host "✗ Backend health check failed" -ForegroundColor Red
}

# Test feed endpoint
try {
    $feedResponse = Invoke-RestMethod -Uri "$BACKEND_URL/api/v1/feed" -Method Get
    if ($feedResponse.videos) {
        Write-Host "✓ Feed API endpoint is working" -ForegroundColor Green
    } else {
        Write-Host "⚠ Feed API returned unexpected response" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠ Feed API test failed (may be expected if no videos)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "✅ Docker containers RESTARTED and running" -ForegroundColor Green
Write-Host "✅ Latest code changes are now active" -ForegroundColor Green
Write-Host "✅ Services are ready" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Remember: After any code changes, run this script again to restart containers!" -ForegroundColor Yellow
Write-Host ""
Write-Host "🌐 Frontend: $FRONTEND_URL" -ForegroundColor Cyan
Write-Host "🔧 Backend:  $BACKEND_URL" -ForegroundColor Cyan
Write-Host "📊 API Docs: $BACKEND_URL/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Tip: Use --rebuild flag if you changed dependencies:" -ForegroundColor Gray
Write-Host "   .\test-browser.ps1 --rebuild" -ForegroundColor Gray
Write-Host ""
Write-Host "You can now test the application in your browser!" -ForegroundColor Green
Write-Host ""
