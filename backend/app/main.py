from fastapi import FastAPI, Depends, HTTPException, Query, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from mangum import Mangum
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import secrets
import os
import boto3
import uuid
import json
import requests
import time

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Import auth dependencies (will be available once Cognito is set up)
try:
    # Try relative import first (for package imports)
    from .auth import requires_auth, optional_auth, get_user_id
    from .social_accounts import SocialAccountManager, SocialPlatform, AccountType
    from .oauth_providers import get_oauth_url, OAuthProviderFactory
    from .social_pages import SocialPagesService
    from .oauth_token_exchange import FacebookTokenExchange, TwitterTokenExchange, TikTokTokenExchange, TokenExchangeError
    from .oauth_state_manager import OAuthStateManager
    from .oauth.facebook_handler import FacebookOAuthHandler
    from .oauth.twitter_handler import TwitterOAuthHandler
    from .oauth.youtube_handler import YouTubeOAuthHandler
    from .oauth.linkedin_handler import LinkedInOAuthHandler
    from .oauth.tiktok_handler import TikTokOAuthHandler
    from .facebook_posting import FacebookPostingService, FacebookPostingError
    from .instagram_posting import InstagramPostingService, InstagramPostingError
    from .s3_upload import S3UploadHelper
    from .upload_requests import create_upload_request, get_upload_request, list_upload_requests, get_request_logs
    AUTH_ENABLED = True
    logger.info("✅ Authentication module loaded successfully (relative import)")
except ImportError:
    try:
        # Fallback to absolute import (for Lambda)
        from auth import requires_auth, optional_auth, get_user_id
        from social_accounts import SocialAccountManager, SocialPlatform, AccountType
        from oauth_providers import get_oauth_url, OAuthProviderFactory
        from social_pages import SocialPagesService
        from oauth_token_exchange import FacebookTokenExchange, TwitterTokenExchange, TikTokTokenExchange, TokenExchangeError
        from oauth_state_manager import OAuthStateManager
        from oauth.facebook_handler import FacebookOAuthHandler
        from oauth.twitter_handler import TwitterOAuthHandler
        from oauth.youtube_handler import YouTubeOAuthHandler
        from oauth.linkedin_handler import LinkedInOAuthHandler
        from oauth.tiktok_handler import TikTokOAuthHandler
        from facebook_posting import FacebookPostingService, FacebookPostingError
        from instagram_posting import InstagramPostingService, InstagramPostingError
        from s3_upload import S3UploadHelper
        from upload_requests import create_upload_request, get_upload_request, list_upload_requests, get_request_logs
        AUTH_ENABLED = True
        logger.info("✅ Authentication module loaded successfully (absolute import)")
    except ImportError as e:
        # Auth not configured yet
        AUTH_ENABLED = False
        requires_auth = None
        optional_auth = None
        get_user_id = None
        SocialAccountManager = None
        SocialPlatform = None
        AccountType = None
        get_oauth_url = None
        OAuthProviderFactory = None
        SocialPagesService = None
        FacebookTokenExchange = None
        TokenExchangeError = None
        logger.warning(f"⚠️ Authentication not loaded: {str(e)}")


# Utility function to convert DynamoDB Decimal objects to native Python types
def convert_decimals(obj):
    """
    Recursively convert Decimal objects to int or float for JSON serialization
    """
    from decimal import Decimal

    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        # Convert to int if it's a whole number, otherwise float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


app = FastAPI(title="ToAllCreation API", version="0.1.0")

# CORS configuration
# Get allowed origins from environment (supports multiple comma-separated origins)
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,  # Cache preflight requests for 10 minutes
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

# Social Media Account Management Endpoints
if AUTH_ENABLED:
    # Initialize OAuth state manager (uses DynamoDB)
    oauth_state_table = os.environ.get('OAUTH_STATE_TABLE', 'toallcreation-oauth-state')
    oauth_state_manager = OAuthStateManager(oauth_state_table)

    @app.get("/api/social/accounts")
    async def list_social_accounts(user_id: str = Depends(get_user_id)):
        """List all connected social media accounts for the user"""
        try:
            accounts = SocialAccountManager.list_accounts(user_id)
            return {
                "accounts": accounts,
                "total": len(accounts)
            }
        except Exception as e:
            logger.error(f"Error listing accounts: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/connect/{platform}")
    async def connect_social_account(
        platform: str,
        request: Request,
        user_id: str = Depends(get_user_id)
    ):
        """
        Initiate OAuth flow to connect a social media account
        Returns authorization URL to redirect user to
        """
        try:
            # Validate platform
            if platform not in ["facebook", "instagram", "twitter", "youtube", "linkedin", "tiktok"]:
                raise HTTPException(status_code=400, detail=f"Unsupported platform: {platform}")

            # Capture origin for redirect after OAuth
            origin = request.headers.get("origin") or request.headers.get("referer")
            if origin and origin.startswith("http://localhost"):
                frontend_url = "http://localhost:5173"
            else:
                frontend_url = os.environ.get('FRONTEND_URL', 'https://d1p7fiwu5m4weh.cloudfront.net')

            # Generate state token for CSRF protection
            state = secrets.token_urlsafe(32)

            # Generate OAuth URL (redirect_uri should point to your callback endpoint)
            # Use the API Gateway URL for the callback
            api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
            redirect_uri = f"{api_base_url}/api/social/callback"
            auth_url = get_oauth_url(platform, redirect_uri, state)

            # For Twitter OAuth 1.0a, the auth_url is a tuple (url, oauth_token_secret)
            # For other platforms, it's just the URL
            if platform == "twitter" and isinstance(auth_url, tuple):
                auth_url, oauth_token_secret = auth_url

                # Extract oauth_token from the auth URL
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(auth_url)
                query_params = parse_qs(parsed_url.query)
                oauth_token = query_params.get('oauth_token', [None])[0]

                # Store oauth_token_secret along with state for callback
                oauth_state_manager.save_state(state, {
                    "user_id": user_id,
                    "platform": platform,
                    "frontend_url": frontend_url,
                    "oauth_token_secret": oauth_token_secret
                })

                # Also store a mapping from oauth_token to state (for OAuth 1.0a callback)
                # Twitter doesn't pass state back, only oauth_token
                if oauth_token:
                    oauth_state_manager.save_state(f"twitter_token_{oauth_token}", {
                        "state": state
                    })
            else:
                # Standard OAuth 2.0 flow
                oauth_state_manager.save_state(state, {
                    "user_id": user_id,
                    "platform": platform,
                    "frontend_url": frontend_url
                })

            return {
                "authorization_url": auth_url,
                "state": state
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error initiating OAuth: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/callback")
    async def oauth_callback(
        code: Optional[str] = Query(None),
        state: Optional[str] = Query(None),
        error: Optional[str] = Query(None),
        oauth_token: Optional[str] = Query(None),  # Twitter OAuth 1.0a
        oauth_verifier: Optional[str] = Query(None),  # Twitter OAuth 1.0a
        denied: Optional[str] = Query(None)  # Twitter OAuth 1.0a denial
    ):
        """
        OAuth callback endpoint
        Called by social platforms after user authorizes
        Supports both OAuth 2.0 (code/state) and OAuth 1.0a (oauth_token/oauth_verifier)
        """
        # Get OAuth state data
        default_frontend = os.environ.get('FRONTEND_URL', 'https://d1p7fiwu5m4weh.cloudfront.net')

        # Handle OAuth 1.0a denial (Twitter)
        if denied:
            logger.error(f"OAuth 1.0a denied: {denied}")
            return RedirectResponse(url=f"{default_frontend}/accounts?error=Authorization+denied")

        # For OAuth 1.0a (Twitter), state is not passed back - look it up from oauth_token
        if not state and oauth_token:
            # Look up state from oauth_token mapping
            token_mapping = oauth_state_manager.get_state(f"twitter_token_{oauth_token}", delete_after_read=True)
            if token_mapping:
                state = token_mapping.get("state")

        if not state:
            raise HTTPException(status_code=400, detail="Missing state parameter")

        oauth_data = oauth_state_manager.get_state(state, delete_after_read=True)

        if not oauth_data:
            raise HTTPException(status_code=400, detail="Invalid or expired state token")

        user_id = oauth_data["user_id"]
        platform = oauth_data["platform"]
        frontend_url = oauth_data.get("frontend_url", default_frontend)

        # Handle OAuth 2.0 errors
        if error:
            logger.error(f"OAuth error: {error}")
            return RedirectResponse(url=f"{frontend_url}/accounts?error={error}")

        try:
            logger.info(f"OAuth callback received for {platform}, user: {user_id}")

            if platform in ["facebook", "instagram"]:
                client_id = os.environ.get("FACEBOOK_CLIENT_ID")
                client_secret = os.environ.get("FACEBOOK_CLIENT_SECRET")
                api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
                redirect_uri = f"{api_base_url}/api/social/callback"

                if not client_id or not client_secret:
                    raise ValueError("Facebook OAuth credentials not configured")

                # Initialize Facebook OAuth handler
                handler = FacebookOAuthHandler(client_id, client_secret, redirect_uri)

                # Exchange code for long-lived access token (60 days)
                tokens = handler.exchange_code(code)
                access_token = tokens.access_token
                expires_in = tokens.expires_in

                # Fetch available accounts (Facebook Pages or Instagram accounts)
                if platform == "facebook":
                    pages = handler.get_pages(access_token)
                else:  # instagram
                    pages = handler.get_instagram_accounts(access_token)

                if not pages:
                    platform_name = "Instagram Business accounts" if platform == "instagram" else "Facebook Pages"
                    return RedirectResponse(
                        url=f"{frontend_url}/accounts?error=No+{platform_name}+found."
                    )

                # Store user's access token temporarily for page fetching (10 min TTL)
                token_key = f"{platform}_token_{user_id}"
                oauth_state_manager.save_state(token_key, {
                    "access_token": access_token,
                    "pages": pages,
                    "expires_at": int(datetime.utcnow().timestamp()) + expires_in
                })

                # Redirect to page selection on frontend
                # Uses the frontend_url captured during OAuth initiation
                return RedirectResponse(url=f"{frontend_url}/accounts?platform={platform}&select_pages=true")

            elif platform == "twitter":
                # Twitter OAuth 1.0a flow using handler
                api_key = os.environ.get("TWITTER_API_KEY")
                api_secret = os.environ.get("TWITTER_API_SECRET")
                api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
                redirect_uri = f"{api_base_url}/api/social/callback"

                if not api_key or not api_secret:
                    raise ValueError("Twitter OAuth credentials not configured")

                if not oauth_token or not oauth_verifier:
                    raise ValueError("Missing OAuth 1.0a parameters (oauth_token, oauth_verifier)")

                # Retrieve oauth_token_secret from state
                oauth_token_secret = oauth_data.get("oauth_token_secret")
                if not oauth_token_secret:
                    raise ValueError("Missing oauth_token_secret in state")

                # Initialize Twitter OAuth handler
                handler = TwitterOAuthHandler(api_key, api_secret, redirect_uri)

                # Exchange request token for access token
                tokens = handler.exchange_code(
                    oauth_token=oauth_token,
                    oauth_verifier=oauth_verifier,
                    oauth_token_secret=oauth_token_secret
                )

                # Get user info
                user_info = handler.get_user_info(
                    access_token=tokens.access_token,
                    access_token_secret=tokens.refresh_token  # Secret is stored in refresh_token field
                )

                # For Twitter, we directly save the account (no page selection needed)
                # Store access_token_secret in refresh_token field (reusing existing field)
                account = SocialAccountManager.create_account(
                    user_id=user_id,
                    platform=platform,
                    platform_user_id=user_info.platform_user_id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,  # Store OAuth 1.0a token secret here
                    token_expires_at=None,  # OAuth 1.0a tokens don't expire
                    account_type="user",
                    username=user_info.username,
                    profile_data=user_info.profile_data
                )

                logger.info(f"Twitter account linked: @{user_info.username}")

                # Redirect back to accounts page with success
                return RedirectResponse(url=f"{frontend_url}/accounts?platform={platform}&success=true")

            elif platform == "youtube":
                # YouTube OAuth 2.0 flow using handler
                client_id = os.environ.get("YOUTUBE_CLIENT_ID")
                # YouTube client secret is stored in SSM Parameter Store (SecureString)
                from ssm_helper import get_youtube_client_secret
                client_secret = get_youtube_client_secret()

                api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
                redirect_uri = f"{api_base_url}/api/social/callback"

                if not client_id or not client_secret:
                    raise ValueError("YouTube OAuth credentials not configured")

                # Initialize YouTube OAuth handler
                handler = YouTubeOAuthHandler(client_id, client_secret, redirect_uri)

                # Exchange code for tokens
                tokens = handler.exchange_code(code)

                # Calculate token expiration
                token_expires_at = int(time.time()) + tokens.expires_in if tokens.expires_in else None

                # Get channel information
                channel_info = handler.get_channel_info(tokens.access_token)

                # Save YouTube account
                account = SocialAccountManager.create_account(
                    user_id=user_id,
                    platform=platform,
                    platform_user_id=channel_info["id"],
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_expires_at=token_expires_at,
                    account_type="user",
                    username=channel_info["title"],
                    profile_data=channel_info
                )

                logger.info(f"YouTube channel linked: {channel_info['title']}")

                # Redirect back to accounts page with success
                return RedirectResponse(url=f"{frontend_url}/accounts?platform={platform}&success=true")

            elif platform == "linkedin":
                # LinkedIn OAuth 2.0 flow using handler
                client_id = os.environ.get("LINKEDIN_CLIENT_ID")
                client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")

                api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
                redirect_uri = f"{api_base_url}/api/social/callback"

                if not client_id or not client_secret:
                    raise ValueError("LinkedIn OAuth credentials not configured")

                # Initialize LinkedIn OAuth handler
                handler = LinkedInOAuthHandler(client_id, client_secret, redirect_uri)

                # Exchange code for tokens
                tokens = handler.exchange_code(code)

                # Calculate token expiration
                token_expires_at = int(time.time()) + tokens.expires_in if tokens.expires_in else None

                # Get user profile information
                user_info = handler.get_user_info(tokens.access_token)

                # Note: Organization posting requires Community Management API access
                # For now, save as personal account
                # TODO: Add organization support once Community Management API is approved

                # Save LinkedIn personal account
                account = SocialAccountManager.create_account(
                    user_id=user_id,
                    platform=platform,
                    platform_user_id=user_info.platform_user_id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_expires_at=token_expires_at,
                    account_type="user",
                    username=user_info.username,
                    profile_data=user_info.profile_data
                )

                logger.info(f"LinkedIn account linked: {user_info.username}")

                # Redirect back to accounts page with success
                return RedirectResponse(url=f"{frontend_url}/accounts?platform={platform}&success=true")

            elif platform == "tiktok":
                # TikTok OAuth 2.0 flow using handler
                client_key = os.environ.get("TIKTOK_CLIENT_ID")
                client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")

                api_base_url = os.environ.get('API_BASE_URL', 'https://50gms3b8y2.execute-api.us-west-2.amazonaws.com')
                redirect_uri = f"{api_base_url}/api/social/callback"

                if not client_key or not client_secret:
                    raise ValueError("TikTok OAuth credentials not configured")

                # Initialize TikTok OAuth handler
                handler = TikTokOAuthHandler(client_key, client_secret, redirect_uri)

                # Exchange code for tokens
                tokens = handler.exchange_code(code)

                # Calculate token expiration
                token_expires_at = int(time.time()) + tokens.expires_in if tokens.expires_in else None

                # Get user profile information
                user_info = handler.get_user_info(tokens.access_token)

                # Save TikTok account
                account = SocialAccountManager.create_account(
                    user_id=user_id,
                    platform=platform,
                    platform_user_id=user_info.platform_user_id,
                    access_token=tokens.access_token,
                    refresh_token=tokens.refresh_token,
                    token_expires_at=token_expires_at,
                    account_type="user",
                    username=user_info.username,
                    profile_data=user_info.profile_data
                )

                logger.info(f"TikTok account linked: {user_info.username}")

                # Redirect back to accounts page with success
                return RedirectResponse(url=f"{frontend_url}/accounts?platform={platform}&success=true")

            else:
                # Other platforms not yet implemented
                logger.warning(f"Token exchange not implemented for {platform}")
                return RedirectResponse(url=f"{frontend_url}/accounts?error=Platform+not+supported")

        except TokenExchangeError as e:
            logger.error(f"Token exchange error: {e}")
            return RedirectResponse(url=f"{frontend_url}/accounts?error={str(e)}")
        except Exception as e:
            logger.error(f"Error processing OAuth callback: {e}")
            return RedirectResponse(url=f"{frontend_url}/accounts?error={str(e)}")

    @app.get("/api/social/pages/{platform}")
    async def get_social_pages(
        platform: str,
        user_id: str = Depends(get_user_id)
    ):
        """
        Get pages/accounts user can post to for a platform
        Called after OAuth to let user select which pages to connect
        """
        try:
            # Get pages from temporary storage (stored during OAuth callback)
            token_key = f"{platform}_token_{user_id}"
            token_data = oauth_state_manager.get_state(token_key, delete_after_read=False)

            if not token_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"No {platform} pages available. Please reconnect your account."
                )

            pages = token_data.get("pages", [])

            return {
                "platform": platform,
                "pages": pages,
                "total": len(pages)
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching pages: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/social/accounts")
    async def save_social_accounts(
        request: Dict[str, Any],
        user_id: str = Depends(get_user_id)
    ):
        """
        Save selected pages/accounts to DynamoDB
        Called after user selects which pages to connect
        """
        try:
            platform = request.get("platform")
            page_ids = request.get("page_ids", [])

            if not platform or not page_ids:
                raise HTTPException(
                    status_code=400,
                    detail="platform and page_ids are required"
                )

            # Get token and pages from temporary storage
            token_key = f"{platform}_token_{user_id}"
            token_data = oauth_state_manager.get_state(token_key, delete_after_read=False)

            if not token_data:
                raise HTTPException(
                    status_code=404,
                    detail="OAuth session expired. Please reconnect your account."
                )

            access_token = token_data.get("access_token")
            available_pages = token_data.get("pages", [])
            expires_at = token_data.get("expires_at")

            # Filter to only selected pages
            pages_to_save = [p for p in available_pages if p["id"] in page_ids]

            if not pages_to_save:
                raise HTTPException(
                    status_code=400,
                    detail="No valid pages selected"
                )

            # Save each page to DynamoDB
            saved_accounts = []
            for page in pages_to_save:
                # For Facebook, use the page-specific access token
                page_token = page.get("access_token", access_token)

                # Handle Instagram vs Facebook pages differently
                if platform == "instagram":
                    account = SocialAccountManager.create_account(
                        user_id=user_id,
                        platform=platform,
                        platform_user_id=page["id"],
                        access_token=page_token,
                        token_expires_at=expires_at,
                        account_type="page",
                        username=page.get("username"),
                        instagram_account_id=page["id"],
                        page_id=page.get("page_id"),  # Store linked Facebook page ID
                        page_name=page.get("page_name")
                    )
                else:
                    account = SocialAccountManager.create_account(
                        user_id=user_id,
                        platform=platform,
                        platform_user_id=page["id"],
                        access_token=page_token,
                        token_expires_at=expires_at,
                        account_type="page",
                        page_id=page["id"],
                        page_name=page["name"]
                    )

                saved_accounts.append({
                    "account_id": account["account_id"],
                    "name": page["name"]
                })

            # Clean up temporary storage
            oauth_state_manager.delete_state(token_key)

            return {
                "message": f"Successfully connected {len(saved_accounts)} {platform} page(s)",
                "accounts": saved_accounts
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/social/accounts/{account_id}")
    async def delete_social_account(
        account_id: str,
        user_id: str = Depends(get_user_id)
    ):
        """Unlink a social media account"""
        try:
            success = SocialAccountManager.delete_account(user_id, account_id)
            if not success:
                raise HTTPException(status_code=404, detail="Account not found")

            return {"message": "Account unlinked successfully"}
        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/social/linkedin/select-organization")
    async def select_linkedin_organization(
        request: Dict[str, Any],
        user_id: str = Depends(get_user_id)
    ):
        """
        Save selected LinkedIn organization page
        Called after user selects which organization to post as
        """
        try:
            state = request.get("state")
            org_id = request.get("org_id")

            if not state or not org_id:
                raise HTTPException(
                    status_code=400,
                    detail="state and org_id are required"
                )

            # Get LinkedIn data from temporary storage
            linkedin_data = oauth_state_manager.get_state(f"linkedin_org_select_{state}", delete_after_read=True)

            if not linkedin_data:
                raise HTTPException(
                    status_code=404,
                    detail="OAuth session expired. Please reconnect your LinkedIn account."
                )

            access_token = linkedin_data.get("access_token")
            token_expires_at = linkedin_data.get("token_expires_at")
            linkedin_id = linkedin_data.get("linkedin_id")
            organizations = linkedin_data.get("organizations", [])

            # Find the selected organization
            selected_org = None
            for org in organizations:
                if org["id"] == org_id:
                    selected_org = org
                    break

            if not selected_org:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid organization selected"
                )

            # Save LinkedIn organization account
            account = SocialAccountManager.create_account(
                user_id=user_id,
                platform="linkedin",
                platform_user_id=linkedin_id,
                access_token=access_token,
                token_expires_at=token_expires_at,
                account_type="organization",
                page_id=org_id,
                page_name=selected_org["name"],
                profile_data={
                    "organization_id": org_id,
                    "organization_name": selected_org["name"],
                    "vanity_name": selected_org.get("vanity_name")
                }
            )

            logger.info(f"LinkedIn organization {selected_org['name']} linked for user {user_id}")

            return {
                "message": f"Successfully connected LinkedIn organization: {selected_org['name']}",
                "account": {
                    "account_id": account["account_id"],
                    "name": selected_org["name"]
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error selecting LinkedIn organization: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/social/upload-url")
    async def get_upload_url(
        request: Dict[str, Any],
        user_id: str = Depends(get_user_id)
    ):
        """
        Generate presigned S3 URL for direct video upload from browser

        Request body:
        - filename: Original filename
        - content_type: MIME type (e.g., "video/mp4")
        """
        try:
            filename = request.get('filename')
            content_type = request.get('content_type', 'video/mp4')

            if not filename:
                raise HTTPException(status_code=400, detail="filename is required")

            # Generate presigned URL
            upload_data = S3UploadHelper.generate_presigned_upload_url(
                user_id=user_id,
                filename=filename,
                content_type=content_type
            )

            return upload_data

        except Exception as e:
            logger.error(f"Error generating upload URL: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/social/post")
    async def post_to_social_media(
        request: Dict[str, Any],
        user_id: str = Depends(get_user_id)
    ):
        """
        Post a video/reel to selected social media accounts (ASYNC)

        Video should already be uploaded to S3 using presigned URL.
        This endpoint queues the posting jobs and returns immediately with a request_id.
        Use the /api/social/uploads/{request_id} endpoint to check status and get results.

        Request body:
        - s3_key: S3 key of uploaded video
        - caption: Post caption
        - account_ids: Array of account IDs to post to

        Returns:
        - request_id: Upload request ID for tracking
        - destinations: List of destinations (platform:account_id) that will be posted to
        - video_url: Public URL of the video
        """
        try:
            s3_key = request.get('s3_key')
            caption = request.get('caption', '')
            account_ids = request.get('account_ids', [])

            if not s3_key:
                raise HTTPException(status_code=400, detail="s3_key is required")

            if not account_ids:
                raise HTTPException(status_code=400, detail="No accounts selected")

            # Generate public URL for the video
            bucket_name = os.environ.get('VIDEO_UPLOAD_BUCKET', 'toallcreation-video-uploads')
            video_url = S3UploadHelper.get_public_url(bucket_name, s3_key)

            logger.info(f"Creating async upload request for video: {video_url}")

            # Build destinations list (account_id is already in format "platform:id")
            destinations = []
            for account_id in account_ids:
                account = SocialAccountManager.get_account(user_id, account_id)
                if account:
                    # account_id is already in the correct format "platform:id"
                    destinations.append(account_id)
                else:
                    logger.warning(f"Account not found: {account_id}")

            if not destinations:
                raise HTTPException(status_code=404, detail="No valid accounts found")

            # Create upload request and queue jobs
            upload_request = create_upload_request(
                user_id=user_id,
                video_url=video_url,
                caption=caption,
                destinations=destinations
            )

            logger.info(f"Upload request created: {upload_request['request_id']}")
            logger.info(f"Queued {len(destinations)} posting jobs")

            # Return immediately with request_id
            return {
                'request_id': upload_request['request_id'],
                'status': 'queued',
                'message': f'Upload request created for {len(destinations)} destination(s)',
                'destinations': destinations,
                'video_url': video_url,
                'created_at': upload_request['created_at']
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating upload request: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/uploads")
    async def list_user_uploads(
        user_id: str = Depends(get_user_id),
        limit: int = Query(5, ge=1, le=100),
        last_key: Optional[str] = Query(None)
    ):
        """
        List all upload requests for the current user

        Query parameters:
        - limit: Maximum number of requests to return (1-100, default: 5)
        - last_key: Pagination token from previous response

        Returns:
        - requests: Array of upload request summaries
        - last_evaluated_key: Pagination token for next page (if more results exist)
        """
        try:
            # Parse pagination token if provided
            last_evaluated_key = None
            if last_key:
                try:
                    last_evaluated_key = json.loads(last_key)
                except:
                    logger.warning(f"Invalid pagination token: {last_key}")

            # Get upload requests
            result = list_upload_requests(
                user_id=user_id,
                limit=limit,
                last_evaluated_key=last_evaluated_key
            )

            # Convert all Decimal objects to native Python types for JSON serialization
            result = convert_decimals(result)

            response = {'requests': result['requests']}

            # Add pagination token if there are more results
            if 'last_evaluated_key' in result:
                response['last_evaluated_key'] = json.dumps(result['last_evaluated_key'])

            return response

        except Exception as e:
            logger.error(f"Error listing upload requests: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/uploads/{request_id}")
    async def get_upload_request_detail(
        request_id: str,
        user_id: str = Depends(get_user_id)
    ):
        """
        Get detailed information about a specific upload request

        Returns:
        - request_id: Upload request ID
        - status: Overall status (queued|processing|completed|failed)
        - video_url: URL of the video
        - caption: Post caption
        - destinations: Dict of destination statuses
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        """
        try:
            # Get the upload request
            upload_request = get_upload_request(request_id)

            if not upload_request:
                raise HTTPException(status_code=404, detail="Upload request not found")

            # Verify the request belongs to the user
            if upload_request.get('user_id') != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Convert all Decimal objects to native Python types for JSON serialization
            return convert_decimals(upload_request)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting upload request: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/social/uploads/{request_id}/logs")
    async def get_upload_request_logs(
        request_id: str,
        user_id: str = Depends(get_user_id),
        destination: Optional[str] = Query(None)
    ):
        """
        Get detailed logs for an upload request

        Query parameters:
        - destination: Optional specific destination (e.g., "instagram:account_id")

        Returns:
        - request_id: Upload request ID
        - overall_status: Overall request status (if destination not specified)
        - destinations: Dict of destination logs (if destination not specified)
        - destination: Specific destination (if destination specified)
        - status: Destination status (if destination specified)
        - logs: Array of log entries
        - error: Error message if failed
        - result: Result data if completed
        """
        try:
            # First verify the request belongs to the user
            upload_request = get_upload_request(request_id)

            if not upload_request:
                raise HTTPException(status_code=404, detail="Upload request not found")

            if upload_request.get('user_id') != user_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Get logs
            logs_data = get_request_logs(request_id, destination)

            if 'error' in logs_data and logs_data['error'] == 'Request not found':
                raise HTTPException(status_code=404, detail="Upload request not found")

            # Convert all Decimal objects to native Python types for JSON serialization
            return convert_decimals(logs_data)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting upload request logs: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Lambda handler
handler = Mangum(app)
