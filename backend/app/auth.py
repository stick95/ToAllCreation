"""
Authentication middleware for AWS Cognito JWT tokens
"""
import os
import json
import time
from typing import Optional, Dict, Any
from functools import lru_cache

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode


# Environment variables
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-west-2")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID", "")
COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")

# Cognito URLs
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

# HTTP Bearer token scheme
security = HTTPBearer()


class CognitoJWKS:
    """
    Manages Cognito JSON Web Key Set (JWKS) for JWT verification
    """
    def __init__(self):
        self.keys = None
        self.last_fetched = 0
        self.cache_ttl = 3600  # 1 hour

    def get_keys(self) -> Dict[str, Any]:
        """
        Fetch Cognito public keys (cached for 1 hour)
        """
        current_time = time.time()

        # Return cached keys if still valid
        if self.keys and (current_time - self.last_fetched) < self.cache_ttl:
            return self.keys

        # Fetch new keys
        try:
            response = requests.get(COGNITO_JWKS_URL, timeout=5)
            response.raise_for_status()
            self.keys = response.json()
            self.last_fetched = current_time
            return self.keys
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to fetch Cognito JWKS: {str(e)}"
            )

    def get_key(self, kid: str) -> Optional[Dict[str, Any]]:
        """
        Get specific key by Key ID (kid)
        """
        keys = self.get_keys()
        for key in keys.get("keys", []):
            if key["kid"] == kid:
                return key
        return None


# Global JWKS manager
jwks_manager = CognitoJWKS()


def verify_jwt_signature(token: str) -> Dict[str, Any]:
    """
    Verify JWT token signature using Cognito public keys

    Returns decoded token claims if valid
    Raises HTTPException if invalid
    """
    try:
        # Get token header without verification
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")

        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'kid' in header"
            )

        # Get public key for this kid
        key = jwks_manager.get_key(kid)
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Public key not found for token"
            )

        # Verify token signature
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER,
            options={"verify_exp": True}
        )

        return claims

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


def verify_token_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify JWT claims are valid

    Checks:
    - Token type is 'access' (not ID token)
    - Token hasn't expired
    - Issuer is correct Cognito User Pool
    - Audience is correct App Client
    """
    # Check token type
    token_use = claims.get("token_use")
    if token_use != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type: {token_use}. Expected 'access' token."
        )

    # Check expiration (already verified by jose.jwt.decode, but double-check)
    exp = claims.get("exp", 0)
    if time.time() >= exp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )

    # Claims are valid
    return claims


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency: Verify JWT token from Authorization header

    Usage:
        @app.get("/protected")
        async def protected_route(user = Depends(verify_token)):
            return {"user_id": user["sub"]}

    Returns:
        Token claims (dict) containing:
        - sub: Cognito user ID (UUID)
        - username: User's username
        - email: User's email (if scope includes email)
        - exp: Expiration timestamp
        - iat: Issued at timestamp
        - token_use: "access"
    """
    token = credentials.credentials

    # Verify signature and decode
    claims = verify_jwt_signature(token)

    # Verify claims
    verify_token_claims(claims)

    return claims


async def requires_auth(
    user: Dict[str, Any] = Depends(verify_token)
) -> Dict[str, Any]:
    """
    FastAPI dependency: Shorthand for requiring authentication

    Usage:
        @app.get("/api/profile")
        async def get_profile(user = Depends(requires_auth)):
            return {"user_id": user["sub"], "username": user["username"]}
    """
    return user


async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency: Optional authentication

    Returns user claims if valid token provided, None otherwise.
    Does not raise exception if token is missing.

    Usage:
        @app.get("/api/posts")
        async def list_posts(user = Depends(optional_auth)):
            if user:
                # Return user-specific posts
                pass
            else:
                # Return public posts
                pass
    """
    if not credentials:
        return None

    try:
        token = credentials.credentials
        claims = verify_jwt_signature(token)
        verify_token_claims(claims)
        return claims
    except HTTPException:
        # Invalid token, but don't raise error for optional auth
        return None


def get_user_id(user: Dict[str, Any] = Depends(requires_auth)) -> str:
    """
    FastAPI dependency: Extract user ID from token

    Usage:
        @app.get("/api/profile")
        async def get_profile(user_id: str = Depends(get_user_id)):
            return {"user_id": user_id}
    """
    return user["sub"]


def get_username(user: Dict[str, Any] = Depends(requires_auth)) -> str:
    """
    FastAPI dependency: Extract username from token
    """
    return user.get("username", user["sub"])


# For testing/debugging
if __name__ == "__main__":
    print(f"Cognito Region: {COGNITO_REGION}")
    print(f"User Pool ID: {COGNITO_USER_POOL_ID}")
    print(f"App Client ID: {COGNITO_APP_CLIENT_ID}")
    print(f"JWKS URL: {COGNITO_JWKS_URL}")
