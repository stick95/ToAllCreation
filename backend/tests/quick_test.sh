#!/bin/bash
# Quick test of auth endpoints (no Cognito required)

echo "Testing Backend Auth Endpoints"
echo "================================"

API_URL="http://localhost:3000"

echo ""
echo "1. Testing public endpoint..."
curl -s $API_URL/health | jq '.'

echo ""
echo "2. Testing protected endpoint WITHOUT token (should show placeholder)..."
curl -s $API_URL/api/profile | jq '.'

echo ""
echo "3. Testing protected endpoint WITH invalid token..."
curl -s -H "Authorization: Bearer fake-token-12345" $API_URL/api/profile | jq '.'

echo ""
echo "4. Testing optional auth endpoint..."
curl -s $API_URL/api/posts | jq '.'

echo ""
echo "================================"
echo "Tests complete!"
echo ""
echo "Note: Auth is not fully enabled yet (Cognito not deployed)"
echo "These tests verify endpoint structure and responses"
