from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from typing import Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import auth dependencies (will be available once Cognito is set up)
try:
    # Try relative import first (for package imports)
    from .auth import requires_auth, optional_auth, get_user_id
    AUTH_ENABLED = True
    logger.info("✅ Authentication module loaded successfully (relative import)")
except ImportError:
    try:
        # Fallback to absolute import (for Lambda)
        from auth import requires_auth, optional_auth, get_user_id
        AUTH_ENABLED = True
        logger.info("✅ Authentication module loaded successfully (absolute import)")
    except ImportError as e:
        # Auth not configured yet
        AUTH_ENABLED = False
        requires_auth = None
        optional_auth = None
        get_user_id = None
        logger.warning(f"⚠️ Authentication not loaded: {str(e)}")

app = FastAPI(title="ToAllCreation API", version="0.1.0")

# CORS configuration for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "ToAllCreation API - Hello World!",
        "version": "0.1.0",
        "status": "operational"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/hello")
def hello():
    return {
        "message": "Hello from the backend!",
        "timestamp": "2025-11-03",
        "service": "ToAllCreation Backend API"
    }

# Protected endpoints (require authentication)
if AUTH_ENABLED:
    @app.get("/api/profile")
    async def get_profile(user: Dict[str, Any] = Depends(requires_auth)):
        """
        Get authenticated user's profile
        Requires: Authorization: Bearer <access_token>
        """
        return {
            "user_id": user["sub"],
            "username": user.get("username", ""),
            "email": user.get("email", ""),
            "auth_time": user.get("auth_time"),
            "token_expires": user.get("exp")
        }

    @app.get("/api/me")
    async def get_me(user_id: str = Depends(get_user_id)):
        """
        Simple endpoint that just returns user ID
        Requires: Authorization: Bearer <access_token>
        """
        return {"user_id": user_id}

    @app.get("/api/posts")
    async def list_posts(user: Dict[str, Any] | None = Depends(optional_auth)):
        """
        List posts - returns different data based on authentication
        Optional authentication (works with or without token)
        """
        if user:
            return {
                "message": "Your private posts",
                "user_id": user["sub"],
                "posts": []  # Would fetch from database
            }
        else:
            return {
                "message": "Public posts only",
                "posts": []  # Would fetch public posts
            }
else:
    # Placeholder endpoints when auth is not configured
    @app.get("/api/profile")
    async def get_profile_placeholder():
        return {
            "message": "Authentication not configured yet",
            "status": "auth_disabled"
        }

# Lambda handler
handler = Mangum(app)
