"""
TikTok OAuth Handler
Handles OAuth 2.0 for TikTok
"""
import requests
from typing import Dict, Any
from .base_handler import OAuthHandler, OAuthTokens, OAuthUserInfo


class TikTokOAuthHandler(OAuthHandler):
    """
    TikTok OAuth 2.0 Handler

    Token Lifecycle:
    - Access tokens: Expire in 24 hours
    - Refresh tokens: Expire in 1 year
    - Must refresh daily for continued access
    """

    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    USERINFO_URL = "https://open.tiktokapis.com/v2/user/info/"
    API_BASE = "https://open.tiktokapis.com/v2"

    def __init__(self, client_key: str, client_secret: str, redirect_uri: str):
        """
        Initialize TikTok OAuth handler

        Args:
            client_key: TikTok app client key
            client_secret: TikTok app client secret
            redirect_uri: OAuth callback URL
        """
        # TikTok uses "client_key" instead of "client_id"
        super().__init__(client_key, client_secret, redirect_uri)
        self.client_key = client_key

    def get_authorization_url(self, state: str = None) -> str:
        """
        Get authorization URL for user consent

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            URL to redirect user to for authorization
        """
        params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.list,video.upload",
            "response_type": "code",
            "redirect_uri": self.redirect_uri
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query_string}"

    def exchange_code(self, code: str, **kwargs) -> OAuthTokens:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from callback

        Returns:
            OAuthTokens with access_token and refresh_token (24 hour expiration)
        """
        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri
            }
        )
        response.raise_for_status()

        data = response.json()

        # Check for error in response
        if data.get("error"):
            error_msg = data.get('error_description', data.get('error', 'Unknown error'))
            raise ValueError(f"TikTok OAuth error: {error_msg}")

        # TikTok v2 API can return tokens either at root level or in "data" field
        # Check if tokens are in a "data" field or at root level
        if "data" in data and isinstance(data["data"], dict) and "access_token" in data["data"]:
            token_data = data["data"]
        else:
            token_data = data

        # Validate required fields exist
        if not token_data.get("access_token"):
            raise ValueError(f"TikTok OAuth: Missing access_token in response. Response: {data}")

        if not token_data.get("refresh_token"):
            raise ValueError(f"TikTok OAuth: Missing refresh_token in response. Response: {data}")

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data.get("expires_in", 86400),  # 24 hours
            token_type="Bearer",
            scope=token_data.get("scope")
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Refresh token from initial authorization

        Returns:
            OAuthTokens with new access_token and refresh_token

        Note:
            TikTok tokens expire every 24 hours and must be refreshed daily
        """
        response = requests.post(
            self.TOKEN_URL,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "client_key": self.client_key,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
        )
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise ValueError(f"TikTok OAuth refresh error: {data.get('error_description', data.get('error'))}")

        # TikTok v2 API can return tokens either at root level or in "data" field
        if "data" in data and isinstance(data["data"], dict) and "access_token" in data["data"]:
            token_data = data["data"]
        else:
            token_data = data

        return OAuthTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data.get("expires_in", 86400),
            token_type="Bearer",
            scope=token_data.get("scope")
        )

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get TikTok user profile information

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with TikTok user ID and profile data
        """
        # TikTok user info API uses GET with query parameters
        fields = "open_id,union_id,avatar_url,display_name"
        url = f"{self.USERINFO_URL}?fields={fields}"

        response = requests.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise ValueError(f"TikTok user info error: {data.get('error_description', data.get('error'))}")

        user_data = data.get("data", {}).get("user", {})

        return OAuthUserInfo(
            platform_user_id=user_data.get("open_id"),
            username=user_data.get("display_name"),
            email=None,  # TikTok doesn't provide email through API
            profile_data=user_data
        )

    def get_video_list(self, access_token: str, max_count: int = 20) -> Dict[str, Any]:
        """
        Get list of user's TikTok videos

        Args:
            access_token: OAuth access token
            max_count: Maximum number of videos to retrieve (default 20, max 20)

        Returns:
            Dict with video list and cursor for pagination
        """
        response = requests.post(
            f"{self.API_BASE}/video/list/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json={
                "max_count": min(max_count, 20)
            }
        )
        response.raise_for_status()

        data = response.json()

        if data.get("error"):
            raise ValueError(f"TikTok video list error: {data.get('error_description', data.get('error'))}")

        return data.get("data", {})
