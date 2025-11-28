# Check Backend Status and Database Tables
Write-Host "=== Backend Container Status ===" -ForegroundColor Cyan
docker compose ps backend

Write-Host "`n=== Backend Logs (Last 30 lines) ===" -ForegroundColor Cyan
docker compose logs backend --tail 30

Write-Host "`n=== Checking Database Tables ===" -ForegroundColor Cyan
docker compose exec -T postgres psql -U short5_user -d short5_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"

Write-Host "`n=== Testing Registration Endpoint ===" -ForegroundColor Cyan
Write-Host "Try registering a user now and check the error response."
Write-Host "If you see a 500 error, check the backend logs above for details."
