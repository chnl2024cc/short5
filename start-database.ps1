# Script to start PostgreSQL database container
Write-Host "Starting PostgreSQL database container..." -ForegroundColor Green

# Check if Docker is running
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Stop and remove existing container if it exists
Write-Host "Cleaning up existing container..." -ForegroundColor Yellow
docker compose down postgres 2>&1 | Out-Null

# Remove volume if it exists (optional - uncomment to reset database)
# docker volume rm short5_swiper_bugagaa_postgres_data 2>&1 | Out-Null

# Start the postgres service
Write-Host "Starting postgres container..." -ForegroundColor Yellow
docker compose up -d postgres

# Wait a moment for container to start
Start-Sleep -Seconds 3

# Check container status
Write-Host "`nContainer Status:" -ForegroundColor Cyan
docker compose ps postgres

# Show logs
Write-Host "`nContainer Logs (last 20 lines):" -ForegroundColor Cyan
docker compose logs postgres --tail 20

# Check if container is healthy
$status = docker compose ps postgres --format json | ConvertFrom-Json
if ($status.Health -eq "healthy") {
    Write-Host "`n✓ Database container is running and healthy!" -ForegroundColor Green
} else {
    Write-Host "`n⚠ Database container may still be starting. Check logs above." -ForegroundColor Yellow
}
