# Test script for Docker build and run
Write-Host "Building Docker image..." -ForegroundColor Green

docker build `
  --build-arg NUXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 `
  --build-arg NUXT_PUBLIC_BACKEND_BASE_URL=http://localhost:8000 `
  -t short5-frontend:test .

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild successful! Starting container..." -ForegroundColor Green
    Write-Host "Container will be available at http://localhost:3000" -ForegroundColor Yellow
    Write-Host "Press Ctrl+C to stop the container`n" -ForegroundColor Yellow
    
    docker run --rm -p 3000:3000 short5-frontend:test
} else {
    Write-Host "`nBuild failed! Check the errors above." -ForegroundColor Red
    exit 1
}
