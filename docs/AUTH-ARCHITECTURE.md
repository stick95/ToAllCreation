# Authentication Architecture

## Overview

ToAllCreation uses **AWS Cognito** for authentication with JWT tokens, integrated with FastAPI backend and React frontend.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │ Login Form   │  │ Register Form│  │ Protected Routes│  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬────────┘  │
│         │                  │                    │           │
│         └──────────────────┴────────────────────┘           │
│                            │                                │
│                  ┌─────────▼─────────┐                      │
│                  │   Auth Context    │                      │
│                  │  (Token Storage)  │                      │
│                  └─────────┬─────────┘                      │
└────────────────────────────┼──────────────────────────────┘
                             │
                    JWT Token (Authorization: Bearer)
                             │
┌────────────────────────────▼──────────────────────────────┐
│              API GATEWAY (HTTP API)                       │
└────────────────────────────┬──────────────────────────────┘
                             │
┌────────────────────────────▼──────────────────────────────┐
│                   AWS LAMBDA (FastAPI)                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │         Auth Middleware (Dependency)             │    │
│  │  - Verify JWT signature                          │    │
│  │  - Decode user claims                            │    │
│  │  - Inject user context                           │    │
│  └─────────────────────┬────────────────────────────┘    │
│                        │                                  │
│  ┌─────────────────────▼────────────────────────────┐    │
│  │            Protected Endpoints                    │    │
│  │  @requires_auth                                   │    │
│  └───────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
                             │
                             │ Validate Token
                             │
┌────────────────────────────▼──────────────────────────────┐
│                      AWS COGNITO                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ User Pool   │  │ User Pool    │  │ JWT Keys       │  │
│  │ (Users)     │  │ Client       │  │ (Public Keys)  │  │
│  └─────────────┘  └──────────────┘  └────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

## Components

### 1. AWS Cognito User Pool

**Purpose:** Manages user accounts, authentication, and JWT token generation

**Configuration:**
- **Pool Name:** `toallcreation-users`
- **Region:** us-west-2
- **Username Attributes:** Email
- **Password Policy:**
  - Minimum length: 8 characters
  - Require uppercase, lowercase, numbers, symbols
- **Email Verification:** Required
- **MFA:** Optional (can enable later)

**User Pool Client:**
- **Client Name:** `toallcreation-web-client`
- **Auth Flows:** USER_PASSWORD_AUTH
- **Token Validity:**
  - Access Token: 1 hour
  - Refresh Token: 30 days
  - ID Token: 1 hour

### 2. Backend Authentication (FastAPI)

**Libraries:**
- `python-jose[cryptography]` - JWT handling
- `pyjwt` - JWT decoding
- `requests` - Fetch Cognito public keys

**Key Components:**

#### Auth Middleware
```python
# backend/app/auth.py
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests

security = HTTPBearer()

def get_cognito_keys():
    """Fetch Cognito public keys for JWT verification"""
    # Cache these keys
    pass

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token from Cognito"""
    token = credentials.credentials
    # Verify signature using Cognito public keys
    # Decode and return user claims
    pass

def requires_auth(user = Depends(verify_token)):
    """Dependency for protected routes"""
    return user
```

#### Protected Endpoints
```python
@app.get("/api/profile")
async def get_profile(user = Depends(requires_auth)):
    return {"user": user}
```

### 3. Frontend Authentication (React)

**Libraries:**
- `amazon-cognito-identity-js` - Official Cognito SDK
- OR `aws-amplify` - Full AWS integration (heavier)
- `zustand` - State management for auth context

**Key Components:**

#### Auth Context
```typescript
// frontend/src/contexts/AuthContext.tsx
interface AuthState {
  user: User | null
  accessToken: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}
```

#### API Client with Token Injection
```typescript
// frontend/src/api/client.ts
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL
})

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await refreshToken()
      return apiClient.request(error.config)
    }
    return Promise.reject(error)
  }
)
```

## Authentication Flows

### 1. Registration Flow

```
User → Frontend Form → Cognito SignUp
                        ↓
                   Send Verification Email
                        ↓
User → Verify Email → Cognito ConfirmSignUp
                        ↓
                   Account Activated
```

**Implementation:**
1. User fills registration form (email, password)
2. Frontend calls `CognitoUser.signUp()`
3. Cognito sends verification email
4. User clicks link, enters code
5. Frontend calls `CognitoUser.confirmRegistration()`

### 2. Login Flow

```
User → Frontend Form → Cognito SignIn
                        ↓
              Return JWT Tokens
              (Access, ID, Refresh)
                        ↓
         Store in localStorage/sessionStorage
                        ↓
         Set Authorization Header
                        ↓
         Access Protected APIs
```

**Implementation:**
1. User enters email/password
2. Frontend calls `CognitoUser.authenticateUser()`
3. Cognito validates credentials
4. Returns JWT tokens (access, id, refresh)
5. Frontend stores tokens securely
6. All API requests include `Authorization: Bearer <token>`

### 3. Token Refresh Flow

```
Access Token Expires (1 hour)
         ↓
API Returns 401 Unauthorized
         ↓
Frontend uses Refresh Token
         ↓
Cognito → New Access Token
         ↓
Retry Original Request
```

**Implementation:**
1. Access token expires after 1 hour
2. Backend returns 401 on protected endpoint
3. Frontend intercepts 401 error
4. Uses refresh token to get new access token
5. Retries original request with new token

### 4. Logout Flow

```
User Clicks Logout
         ↓
Clear Local Tokens
         ↓
Call Cognito GlobalSignOut (optional)
         ↓
Redirect to Login
```

## Security Considerations

### 1. Token Storage

**Options:**
- **localStorage** - Persistent, survives browser restart (XSS vulnerable)
- **sessionStorage** - Cleared on tab close (more secure)
- **httpOnly Cookie** - Best security, requires backend support

**Recommendation:** Use `sessionStorage` for tokens in MVP, migrate to httpOnly cookies in production.

### 2. CORS Configuration

Backend must allow frontend origin:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://d1p7fiwu5m4weh.cloudfront.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. JWT Validation

**Backend MUST:**
- Verify JWT signature using Cognito public keys
- Check token expiration (`exp` claim)
- Validate issuer (`iss` claim)
- Validate audience (`aud` claim)

### 4. Password Security

Cognito handles:
- Password hashing (bcrypt)
- Brute-force protection
- Password reset flow

### 5. HTTPS Only

All authentication traffic MUST use HTTPS:
- CloudFront distribution (already configured)
- API Gateway (AWS enforces HTTPS)

## AWS Free Tier Impact

**Cognito Free Tier:**
- **50,000 Monthly Active Users (MAUs)** - FREE forever
- Additional users: $0.0055 per MAU

**For ToAllCreation:**
- Expected users in Year 1: < 100
- **Cost: $0/month** ✅

## Environment Variables

### Backend (Lambda)
```yaml
# backend/template.yaml
Environment:
  Variables:
    COGNITO_USER_POOL_ID: !Ref UserPool
    COGNITO_APP_CLIENT_ID: !Ref UserPoolClient
    COGNITO_REGION: us-west-2
```

### Frontend
```env
# frontend/.env.production
VITE_COGNITO_USER_POOL_ID=us-west-2_XXXXXXXXX
VITE_COGNITO_CLIENT_ID=XXXXXXXXXXXXXXXXXX
VITE_COGNITO_REGION=us-west-2
VITE_API_URL=https://50gms3b8y2.execute-api.us-west-2.amazonaws.com
```

## Database Schema (DynamoDB)

**User Profile Table:**
```
users
├── userId (String, PK) - Cognito sub claim
├── email (String, GSI)
├── displayName (String)
├── createdAt (Number, timestamp)
├── lastLogin (Number, timestamp)
└── settings (Map)
    ├── emailNotifications (Boolean)
    └── ...
```

**Note:** Cognito stores authentication data. DynamoDB stores application-specific user data.

## API Endpoints

### Public (No Auth Required)
- `POST /auth/register` - Proxy to Cognito SignUp
- `POST /auth/login` - Proxy to Cognito Login
- `POST /auth/verify-email` - Confirm email
- `POST /auth/forgot-password` - Initiate password reset
- `POST /auth/reset-password` - Complete password reset
- `GET /health` - Health check

### Protected (Auth Required)
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile
- `POST /api/posts` - Create post (future)
- `GET /api/posts` - List user's posts (future)

## Implementation Phases

### Phase 1: Infrastructure (Week 1)
- [ ] Add Cognito to SAM template
- [ ] Deploy User Pool and Client
- [ ] Configure environment variables

### Phase 2: Backend Auth (Week 1-2)
- [ ] Install dependencies (python-jose, pyjwt)
- [ ] Create auth.py middleware
- [ ] Add public auth endpoints (login, register)
- [ ] Add protected test endpoint
- [ ] Test with Postman/curl

### Phase 3: Frontend Auth (Week 2)
- [ ] Install Cognito SDK
- [ ] Create AuthContext with Zustand
- [ ] Build Login component
- [ ] Build Register component
- [ ] Add token interceptor to API client
- [ ] Add ProtectedRoute component

### Phase 4: Integration (Week 2)
- [ ] End-to-end testing
- [ ] Error handling
- [ ] Loading states
- [ ] Token refresh logic

### Phase 5: Polish (Week 3)
- [ ] Password reset flow
- [ ] Email verification UI
- [ ] Profile page
- [ ] Logout everywhere
- [ ] Security audit

## Testing Strategy

### Unit Tests
- JWT token parsing and validation
- Auth middleware logic
- Frontend auth context state management

### Integration Tests
- Full registration flow
- Login → API call → Logout
- Token refresh mechanism
- Invalid token handling

### Security Tests
- SQL injection attempts (N/A for Cognito)
- XSS attempts in auth forms
- CSRF protection
- Token expiration enforcement

## Rollback Plan

If authentication breaks production:

1. **Feature Flag:** Disable auth requirement temporarily
2. **Revert:** Git revert auth commits
3. **Hotfix:** Deploy previous stable version
4. **Debug:** Test in staging environment

## References

- [AWS Cognito Developer Guide](https://docs.aws.amazon.com/cognito/latest/developerguide/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - JWT debugger
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

**Next Steps:** Implement this architecture in SAM template and backend code.
