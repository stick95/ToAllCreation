#!/bin/bash

# Manual Authentication Testing Script
# Tests backend authentication endpoints with curl

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:3000}"

echo "================================================"
echo "Backend Authentication Manual Testing"
echo "================================================"
echo "API URL: $API_URL"
echo ""

# Test 1: Public endpoints (should work)
echo -e "${YELLOW}Test 1: Public Endpoints (No Auth Required)${NC}"
echo "GET /"
response=$(curl -s -w "\n%{http_code}" "$API_URL/")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✓ Root endpoint: $status${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Root endpoint failed: $status${NC}"
fi
echo ""

echo "GET /health"
response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✓ Health endpoint: $status${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Health endpoint failed: $status${NC}"
fi
echo ""

# Test 2: Protected endpoint without token (should fail with 403)
echo -e "${YELLOW}Test 2: Protected Endpoint Without Token${NC}"
echo "GET /api/profile (no Authorization header)"
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/profile")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" = "403" ]; then
    echo -e "${GREEN}✓ Correctly rejected: $status${NC}"
    echo "$body" | jq '.'
elif [ "$status" = "200" ]; then
    echo -e "${YELLOW}⚠ Auth not enabled yet (placeholder response)${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Unexpected status: $status${NC}"
    echo "$body"
fi
echo ""

# Test 3: Protected endpoint with invalid token (should fail with 401)
echo -e "${YELLOW}Test 3: Protected Endpoint With Invalid Token${NC}"
echo "GET /api/profile (Authorization: Bearer invalid-token)"
response=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer invalid-token-here" \
    "$API_URL/api/profile")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid token: $status${NC}"
    echo "$body" | jq '.'
elif [ "$status" = "200" ]; then
    echo -e "${YELLOW}⚠ Auth not enabled yet (placeholder response)${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Unexpected status: $status${NC}"
    echo "$body"
fi
echo ""

# Test 4: Optional auth endpoint without token (should work)
echo -e "${YELLOW}Test 4: Optional Auth Endpoint Without Token${NC}"
echo "GET /api/posts (no Authorization header)"
response=$(curl -s -w "\n%{http_code}" "$API_URL/api/posts")
status=$(echo "$response" | tail -n 1)
body=$(echo "$response" | sed '$d')

if [ "$status" = "200" ]; then
    echo -e "${GREEN}✓ Works without auth: $status${NC}"
    echo "$body" | jq '.'
else
    echo -e "${RED}✗ Failed: $status${NC}"
    echo "$body"
fi
echo ""

# Test 5: With real Cognito token (if provided)
if [ -n "$COGNITO_TOKEN" ]; then
    echo -e "${YELLOW}Test 5: Protected Endpoint With Real Token${NC}"
    echo "GET /api/profile (Authorization: Bearer <real-token>)"
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $COGNITO_TOKEN" \
        "$API_URL/api/profile")
    status=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✓ Successfully authenticated: $status${NC}"
        echo "$body" | jq '.'
    else
        echo -e "${RED}✗ Failed: $status${NC}"
        echo "$body"
    fi
    echo ""
else
    echo -e "${YELLOW}Test 5: Skipped (No COGNITO_TOKEN provided)${NC}"
    echo "To test with real token:"
    echo "  COGNITO_TOKEN=<your-token> ./manual_auth_test.sh"
    echo ""
fi

echo "================================================"
echo "Testing Complete"
echo "================================================"
echo ""
echo "Next Steps:"
echo "1. Deploy Cognito User Pool (see docs/AUTH-ARCHITECTURE.md)"
echo "2. Register a test user"
echo "3. Get access token from Cognito"
echo "4. Run: COGNITO_TOKEN=<token> ./manual_auth_test.sh"
