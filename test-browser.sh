#!/bin/bash
# Browser Testing Script for Short-Video Platform
# This script ALWAYS restarts Docker containers and tests the application
# 
# IMPORTANT: Since we're developing in Docker containers, code changes require
# container restarts to take effect. This script ensures a clean restart every time.
#
# Usage: ./test-browser.sh [--rebuild]
#   --rebuild: Rebuild Docker images before starting (use when dependencies change)

set -e

# Parse arguments
REBUILD=false
if [[ "$1" == "--rebuild" ]]; then
    REBUILD=true
fi

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧪 Starting Browser Test Suite...${NC}"
echo -e "${CYAN}==================================${NC}"
echo -e "${YELLOW}⚠️  IMPORTANT: This script will RESTART all Docker containers${NC}"
echo -e "${YELLOW}   Code changes require container restarts in Docker development!${NC}"
echo ""

# Configuration
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"
MAX_WAIT=60  # Maximum wait time in seconds

# Step 1: Stop all containers (CRITICAL - ensures clean state)
echo -e "${YELLOW}Step 1: Stopping all Docker containers...${NC}"
echo -e "${GRAY}  This ensures a clean restart with latest code changes...${NC}"
if docker compose down; then
    echo -e "${GREEN}✓ All containers stopped${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Some containers may not have stopped cleanly${NC}"
    echo -e "${GRAY}   Continuing anyway...${NC}"
fi

# Step 2: Rebuild images if requested (for dependency changes)
if [ "$REBUILD" = true ]; then
    echo ""
    echo -e "${YELLOW}Step 2a: Rebuilding Docker images (--rebuild flag detected)...${NC}"
    echo -e "${GRAY}  This may take a few minutes...${NC}"
    if ! docker compose build --no-cache; then
        echo -e "${RED}✗ Failed to rebuild images${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Images rebuilt successfully${NC}"
fi

# Step 2/3: Start containers (CRITICAL - loads latest code)
STEP_NUM=$([ "$REBUILD" = true ] && echo "3" || echo "2")
echo ""
echo -e "${YELLOW}Step $STEP_NUM: Starting Docker containers with latest code...${NC}"
echo -e "${GRAY}  This will load all recent code changes...${NC}"
if ! docker compose up -d; then
    echo -e "${RED}✗ Failed to start containers${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Containers started${NC}"

# Verify containers are actually running
echo ""
echo -e "${GRAY}Verifying containers are running...${NC}"
sleep 2
RUNNING_COUNT=$(docker compose ps --format json | jq -r 'select(.State == "running")' | wc -l)
EXPECTED_COUNT=6  # frontend, backend, postgres, redis, celery_worker, video_worker

if [ "$RUNNING_COUNT" -lt "$EXPECTED_COUNT" ]; then
    echo -e "${YELLOW}⚠️  Warning: Only $RUNNING_COUNT containers are running (expected $EXPECTED_COUNT)${NC}"
    echo -e "${GRAY}   Checking container status...${NC}"
    docker compose ps
else
    echo -e "${GREEN}✓ All containers are running${NC}"
fi

echo -e "${YELLOW}Step 3: Waiting for services to be ready...${NC}"

# Wait for backend to be ready
echo "Waiting for backend ($BACKEND_URL)..."
for i in $(seq 1 $MAX_WAIT); do
  if curl -s -f "$BACKEND_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is ready${NC}"
    break
  fi
  if [ $i -eq $MAX_WAIT ]; then
    echo -e "${RED}✗ Backend failed to start after $MAX_WAIT seconds${NC}"
    exit 1
  fi
  sleep 1
done

# Wait for frontend to be ready
echo "Waiting for frontend ($FRONTEND_URL)..."
for i in $(seq 1 $MAX_WAIT); do
  if curl -s -f "$FRONTEND_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is ready${NC}"
    break
  fi
  if [ $i -eq $MAX_WAIT ]; then
    echo -e "${RED}✗ Frontend failed to start after $MAX_WAIT seconds${NC}"
    exit 1
  fi
  sleep 1
done

# Give services a moment to fully initialize
sleep 3

STEP_NUM=$([ "$REBUILD" = true ] && echo "5" || echo "4")
echo ""
echo -e "${YELLOW}Step $STEP_NUM: Checking TypeScript errors...${NC}"
echo -e "${GRAY}  Validating code changes are type-safe...${NC}"

# Check for TypeScript errors in frontend
cd frontend
if npm run typecheck 2>&1 | grep -q "error TS"; then
    echo -e "${RED}✗ TypeScript errors found!${NC}"
    echo -e "${RED}TypeScript errors:${NC}"
    npm run typecheck 2>&1 | grep "error TS" | head -10
    echo ""
    echo -e "${YELLOW}⚠ Please fix TypeScript errors before proceeding!${NC}"
    cd ..
    exit 1
else
    echo -e "${GREEN}✓ No TypeScript errors found${NC}"
fi
cd ..

STEP_NUM=$([ "$REBUILD" = true ] && echo "6" || echo "5")
echo ""
echo -e "${YELLOW}Step $STEP_NUM: Testing API endpoints...${NC}"
echo -e "${GRAY}  Verifying services respond correctly after restart...${NC}"

# Test backend health
if curl -s "$BACKEND_URL/health" | grep -q "healthy"; then
  echo -e "${GREEN}✓ Backend health check passed${NC}"
else
  echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Test feed endpoint
FEED_RESPONSE=$(curl -s "$BACKEND_URL/api/v1/feed")
if echo "$FEED_RESPONSE" | grep -q "videos"; then
  echo -e "${GREEN}✓ Feed API endpoint is working${NC}"
else
  echo -e "${YELLOW}⚠ Feed API returned unexpected response${NC}"
fi

echo ""
echo -e "${GREEN}=================================="
echo "✅ Docker containers RESTARTED and running"
echo "✅ Latest code changes are now active"
echo "✅ Services are ready"
echo "=================================="
echo ""
echo -e "${YELLOW}📝 Remember: After any code changes, run this script again to restart containers!${NC}"
echo ""
echo -e "${CYAN}🌐 Frontend: $FRONTEND_URL${NC}"
echo -e "${CYAN}🔧 Backend:  $BACKEND_URL${NC}"
echo -e "${CYAN}📊 API Docs: $BACKEND_URL/docs${NC}"
echo ""
echo -e "${GRAY}💡 Tip: Use --rebuild flag if you changed dependencies:${NC}"
echo -e "${GRAY}   ./test-browser.sh --rebuild${NC}"
echo ""
echo -e "${GREEN}You can now test the application in your browser!${NC}"
echo ""
