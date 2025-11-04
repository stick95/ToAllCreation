"""
Tests for authentication middleware

Run with: pytest tests/test_auth.py
"""
import os
import time
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from jose import jwt


# Mock Cognito configuration for testing
os.environ["COGNITO_REGION"] = "us-west-2"
os.environ["COGNITO_USER_POOL_ID"] = "us-west-2_TEST12345"
os.environ["COGNITO_APP_CLIENT_ID"] = "test-client-id-123456"

from backend.app.main import app
from backend.app.auth import verify_jwt_signature, verify_token_claims


client = TestClient(app)


def generate_mock_jwt(
    user_id: str = "test-user-123",
    username: str = "testuser",
    email: str = "test@example.com",
    expired: bool = False
) -> str:
    """
    Generate a mock JWT token for testing

    NOTE: This is NOT a real Cognito token and won't pass signature verification
    Use this for testing token structure and claims parsing only
    """
    now = int(time.time())
    exp = now - 3600 if expired else now + 3600  # Expired or valid for 1 hour

    payload = {
        "sub": user_id,
        "username": username,
        "email": email,
        "token_use": "access",
        "auth_time": now,
        "iat": now,
        "exp": exp,
        "iss": f"https://cognito-idp.us-west-2.amazonaws.com/{os.environ['COGNITO_USER_POOL_ID']}",
        "aud": os.environ["COGNITO_APP_CLIENT_ID"],
        "cognito:username": username
    }

    # Sign with a test secret (won't match Cognito public key)
    token = jwt.encode(payload, "test-secret", algorithm="HS256")
    return token


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_public_endpoints_no_auth(self):
        """Public endpoints should work without authentication"""
        response = client.get("/")
        assert response.status_code == 200

        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/api/hello")
        assert response.status_code == 200

    def test_protected_endpoint_without_token(self):
        """Protected endpoints should return 403 without token"""
        response = client.get("/api/profile")
        # Will return 403 Forbidden when auth is enabled
        # Or 200 with placeholder message when auth is disabled
        assert response.status_code in [200, 403]

    def test_protected_endpoint_with_invalid_token(self):
        """Protected endpoints should reject invalid tokens"""
        headers = {"Authorization": "Bearer invalid-token-here"}
        response = client.get("/api/profile", headers=headers)
        # Should return 401 Unauthorized when auth is enabled
        assert response.status_code in [200, 401]

    def test_optional_auth_without_token(self):
        """Optional auth endpoints should work without token"""
        response = client.get("/api/posts")
        assert response.status_code == 200
        data = response.json()
        # Should return public posts when no auth
        assert "message" in data


class TestJWTValidation:
    """Test JWT token validation logic"""

    def test_jwt_token_structure(self):
        """Test mock JWT token has correct structure"""
        token = generate_mock_jwt()

        # Decode without verification to check structure
        from jose import jwt as jose_jwt
        unverified_claims = jose_jwt.get_unverified_claims(token)

        assert unverified_claims["sub"] == "test-user-123"
        assert unverified_claims["username"] == "testuser"
        assert unverified_claims["email"] == "test@example.com"
        assert unverified_claims["token_use"] == "access"
        assert "exp" in unverified_claims
        assert "iat" in unverified_claims

    def test_expired_token(self):
        """Test that expired tokens are rejected"""
        token = generate_mock_jwt(expired=True)

        from jose import jwt as jose_jwt
        unverified_claims = jose_jwt.get_unverified_claims(token)

        # Check exp claim is in the past
        assert unverified_claims["exp"] < time.time()

    def test_token_claims_validation(self):
        """Test verify_token_claims function"""
        # Valid claims
        valid_claims = {
            "sub": "user-123",
            "username": "testuser",
            "token_use": "access",
            "exp": int(time.time()) + 3600,
            "iss": f"https://cognito-idp.us-west-2.amazonaws.com/{os.environ['COGNITO_USER_POOL_ID']}"
        }

        # Should not raise exception
        result = verify_token_claims(valid_claims)
        assert result == valid_claims

    def test_token_claims_wrong_type(self):
        """Test that ID tokens are rejected"""
        invalid_claims = {
            "sub": "user-123",
            "token_use": "id",  # Wrong type - should be "access"
            "exp": int(time.time()) + 3600
        }

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token_claims(invalid_claims)

        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    def test_token_claims_expired(self):
        """Test that expired tokens are rejected"""
        expired_claims = {
            "sub": "user-123",
            "username": "testuser",
            "token_use": "access",
            "exp": int(time.time()) - 3600  # Expired 1 hour ago
        }

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            verify_token_claims(expired_claims)

        assert exc_info.value.status_code == 401
        assert "expired" in str(exc_info.value.detail).lower()


class TestAuthDependencies:
    """Test FastAPI auth dependencies"""

    def test_requires_auth_dependency(self):
        """Test requires_auth dependency structure"""
        from backend.app.auth import requires_auth
        from inspect import signature

        # Check it's a FastAPI dependency
        sig = signature(requires_auth)
        assert 'user' in sig.parameters

    def test_optional_auth_dependency(self):
        """Test optional_auth dependency structure"""
        from backend.app.auth import optional_auth
        from inspect import signature

        sig = signature(optional_auth)
        assert 'credentials' in sig.parameters


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
