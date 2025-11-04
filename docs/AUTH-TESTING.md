# Authentication Testing Guide

## Overview

This guide explains how to test the backend authentication system at different stages of implementation.

## Testing Phases

### Phase 1: Code Structure Tests (No Cognito Required)
**Status:** ✅ Available now
**Purpose:** Test auth middleware code structure and logic

### Phase 2: Manual API Tests (No Cognito Required)
**Status:** ✅ Available now
**Purpose:** Test public/protected endpoint responses

### Phase 3: Full Integration Tests (Cognito Required)
**Status:** ⏳ After Cognito deployment
**Purpose:** Test with real JWT tokens from Cognito

---

## Phase 1: Code Structure Tests

### Run Unit Tests

```bash
cd backend

# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest tests/test_auth.py -v

# Run with coverage
pytest tests/test_auth.py --cov=app --cov-report=html
```

### What These Tests Cover

- ✅ JWT token structure validation
- ✅ Token claims parsing
- ✅ Expired token detection
- ✅ Invalid token type rejection (ID vs Access tokens)
- ✅ FastAPI dependency structure
- ✅ Public endpoint accessibility
- ✅ Protected endpoint behavior

### Example Output

```
tests/test_auth.py::TestAuthEndpoints::test_public_endpoints_no_auth PASSED
tests/test_auth.py::TestAuthEndpoints::test_protected_endpoint_without_token PASSED
tests/test_auth.py::TestJWTValidation::test_jwt_token_structure PASSED
tests/test_auth.py::TestJWTValidation::test_expired_token PASSED
tests/test_auth.py::TestJWTValidation::test_token_claims_validation PASSED
tests/test_auth.py::TestJWTValidation::test_token_claims_wrong_type PASSED

====== 12 passed in 2.45s ======
```

---

## Phase 2: Manual API Tests

### Start Local Backend

```bash
cd backend
sam build
sam local start-api --port 3000
```

### Run Manual Test Script

```bash
# From project root
./backend/tests/manual_auth_test.sh

# Or specify custom API URL
API_URL=https://your-api-url.com ./backend/tests/manual_auth_test.sh
```

### What This Tests

✅ **Test 1: Public Endpoints**
- GET / (root)
- GET /health
- GET /api/hello
- **Expected:** 200 OK

✅ **Test 2: Protected Without Token**
- GET /api/profile (no Authorization header)
- **Expected:** 403 Forbidden (or 200 with placeholder if auth not enabled)

✅ **Test 3: Protected With Invalid Token**
- GET /api/profile (Authorization: Bearer invalid-token)
- **Expected:** 401 Unauthorized (or 200 with placeholder if auth not enabled)

✅ **Test 4: Optional Auth Without Token**
- GET /api/posts (no Authorization header)
- **Expected:** 200 OK with public posts message

### Example Output

```
================================================
Backend Authentication Manual Testing
================================================
API URL: http://localhost:3000

Test 1: Public Endpoints (No Auth Required)
GET /
✓ Root endpoint: 200
{
  "message": "ToAllCreation API - Hello World!",
  "version": "0.1.0",
  "status": "operational"
}

Test 2: Protected Endpoint Without Token
GET /api/profile (no Authorization header)
⚠ Auth not enabled yet (placeholder response)
{
  "message": "Authentication not configured yet",
  "status": "auth_disabled"
}

================================================
Testing Complete
================================================
```

### Manual curl Tests

```bash
# Test public endpoint
curl http://localhost:3000/

# Test health check
curl http://localhost:3000/health

# Test protected endpoint without token (should fail)
curl http://localhost:3000/api/profile

# Test protected endpoint with fake token (should fail)
curl -H "Authorization: Bearer fake-token" \
  http://localhost:3000/api/profile

# Test optional auth endpoint
curl http://localhost:3000/api/posts
```

---

## Phase 3: Full Integration Tests (With Cognito)

### Prerequisites

1. ✅ Cognito User Pool deployed
2. ✅ User Pool Client configured
3. ✅ Environment variables set
4. ✅ At least one test user registered

### Step 1: Register Test User

```bash
# Using Python script
python backend/tests/get_cognito_token.py \
  --email test@example.com \
  --password TestPassword123! \
  --register

# Or using AWS CLI
aws cognito-idp sign-up \
  --region us-west-2 \
  --client-id YOUR_CLIENT_ID \
  --username test@example.com \
  --password TestPassword123! \
  --user-attributes Name=email,Value=test@example.com
```

### Step 2: Verify Email

```bash
# Verify with code from email
aws cognito-idp confirm-sign-up \
  --region us-west-2 \
  --client-id YOUR_CLIENT_ID \
  --username test@example.com \
  --confirmation-code 123456

# Or admin-confirm (skip email verification)
aws cognito-idp admin-confirm-sign-up \
  --region us-west-2 \
  --user-pool-id YOUR_USER_POOL_ID \
  --username test@example.com
```

### Step 3: Get Access Token

```bash
# Using Python script
python backend/tests/get_cognito_token.py \
  --email test@example.com \
  --password TestPassword123!

# Script will output:
# export COGNITO_TOKEN="eyJraWQ..."
```

### Step 4: Test With Real Token

```bash
# Export token from script output
export COGNITO_TOKEN="eyJraWQiOiJ..."

# Test protected endpoint
curl -H "Authorization: Bearer $COGNITO_TOKEN" \
  http://localhost:3000/api/profile

# Expected response:
# {
#   "user_id": "uuid-here",
#   "username": "test@example.com",
#   "email": "test@example.com",
#   "auth_time": 1699046400,
#   "token_expires": 1699050000
# }
```

### Step 5: Run Full Test Suite

```bash
# Run manual tests with real token
COGNITO_TOKEN="$COGNITO_TOKEN" \
  ./backend/tests/manual_auth_test.sh
```

### Expected Results

```
Test 5: Protected Endpoint With Real Token
GET /api/profile (Authorization: Bearer <real-token>)
✓ Successfully authenticated: 200
{
  "user_id": "abc123...",
  "username": "test@example.com",
  "email": "test@example.com",
  "auth_time": 1699046400,
  "token_expires": 1699050000
}
```

---

## Testing Different Scenarios

### Test 1: Expired Token

```bash
# Wait for token to expire (1 hour) or manually modify exp claim
curl -H "Authorization: Bearer $EXPIRED_TOKEN" \
  http://localhost:3000/api/profile

# Expected: 401 Unauthorized
# {"detail": "Token has expired"}
```

### Test 2: Wrong Token Type

```bash
# Use ID token instead of access token
curl -H "Authorization: Bearer $ID_TOKEN" \
  http://localhost:3000/api/profile

# Expected: 401 Unauthorized
# {"detail": "Invalid token type: id. Expected 'access' token."}
```

### Test 3: Malformed Token

```bash
curl -H "Authorization: Bearer not-a-jwt-token" \
  http://localhost:3000/api/profile

# Expected: 401 Unauthorized
# {"detail": "Invalid token: ..."}
```

### Test 4: Missing Authorization Header

```bash
curl http://localhost:3000/api/profile

# Expected: 403 Forbidden
# {"detail": "Not authenticated"}
```

### Test 5: Optional Auth Endpoints

```bash
# Without token
curl http://localhost:3000/api/posts
# {"message": "Public posts only", "posts": []}

# With token
curl -H "Authorization: Bearer $COGNITO_TOKEN" \
  http://localhost:3000/api/posts
# {"message": "Your private posts", "user_id": "...", "posts": []}
```

---

## Integration Test Checklist

After Cognito is deployed, verify all these scenarios:

### Authentication Flow
- [ ] Register new user
- [ ] Verify email
- [ ] Login and get tokens
- [ ] Access protected endpoint with valid token
- [ ] Refresh token after expiration

### Token Validation
- [ ] Valid token accepted
- [ ] Expired token rejected (401)
- [ ] Invalid signature rejected (401)
- [ ] Wrong token type rejected (401)
- [ ] Malformed token rejected (401)
- [ ] Missing token rejected (403)

### Endpoint Protection
- [ ] Public endpoints work without token
- [ ] Protected endpoints require valid token
- [ ] Optional auth endpoints work both ways

### Error Handling
- [ ] Clear error messages for each failure type
- [ ] Proper HTTP status codes
- [ ] No sensitive info in error responses

### Performance
- [ ] JWKS keys cached (not fetched on every request)
- [ ] Token verification is fast (< 10ms)
- [ ] No unnecessary Cognito API calls

---

## Troubleshooting

### "Authentication not configured yet"

**Problem:** Auth middleware not loaded
**Solution:** Set Cognito environment variables:
```bash
export COGNITO_USER_POOL_ID="us-west-2_XXXXXXXXX"
export COGNITO_APP_CLIENT_ID="XXXXXXXXXXXXXXXXX"
export COGNITO_REGION="us-west-2"
```

### "Failed to fetch Cognito JWKS"

**Problem:** Can't reach Cognito JWKS endpoint
**Solution:** Check internet connectivity and User Pool ID

### "Public key not found for token"

**Problem:** Token signed with key not in JWKS
**Solution:**
- Wait 1 hour for JWKS cache to refresh
- Restart Lambda (clears cache)
- Verify token is from correct User Pool

### "Invalid token: Signature verification failed"

**Problem:** Token signature doesn't match Cognito public key
**Solution:**
- Ensure token is fresh (not manually modified)
- Verify User Pool ID matches
- Check token was generated by correct App Client

### "Token has expired"

**Problem:** Access token lifetime exceeded (default 1 hour)
**Solution:**
- Get fresh token
- Use refresh token to get new access token
- Check token exp claim: `jwt decode <token> | jq .exp`

---

## Automated Testing (Future)

### Pytest Integration Tests

```python
# tests/integration/test_auth_flow.py
def test_full_auth_flow():
    # Register user
    # Verify email
    # Login
    # Get token
    # Call protected endpoint
    # Verify response
    pass
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/test.yml
- name: Run Auth Tests
  env:
    COGNITO_USER_POOL_ID: ${{ secrets.TEST_USER_POOL_ID }}
    COGNITO_APP_CLIENT_ID: ${{ secrets.TEST_APP_CLIENT_ID }}
  run: |
    pytest tests/test_auth.py
```

---

## Security Testing

### OWASP Top 10 Checks

- [ ] **A01: Broken Access Control** - Protected endpoints require valid auth
- [ ] **A02: Cryptographic Failures** - JWT signatures verified
- [ ] **A03: Injection** - No SQL/command injection (using Cognito)
- [ ] **A04: Insecure Design** - Proper token expiration
- [ ] **A05: Security Misconfiguration** - HTTPS enforced
- [ ] **A06: Vulnerable Components** - Dependencies up to date
- [ ] **A07: Authentication Failures** - Strong password policy
- [ ] **A08: Data Integrity Failures** - JWT tampering detected
- [ ] **A09: Logging Failures** - Auth events logged
- [ ] **A10: SSRF** - No external URL in tokens

### Penetration Testing

```bash
# Test with modified token
python -c "import jwt; print(jwt.encode({'sub': 'fake'}, 'wrong-key'))"

# Test with SQL injection in username
curl -H "Authorization: Bearer '; DROP TABLE users; --" \
  http://localhost:3000/api/profile

# Test with XSS in token claims
# (Should be sanitized before displaying)
```

---

## Next Steps

1. ✅ Run Phase 1 & 2 tests now (no Cognito needed)
2. ⏳ Deploy Cognito User Pool (Phase 4)
3. ⏳ Run Phase 3 tests with real tokens
4. ⏳ Add automated integration tests
5. ⏳ Security audit

## References

- [AWS Cognito Testing Best Practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-testing.html)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [JWT Testing Tools](https://jwt.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
