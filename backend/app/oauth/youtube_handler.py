"""
YouTube OAuth Handler
Handles OAuth 2.0 for YouTube (Google OAuth)
"""
import requests
from typing import Dict, Any
from .base_handler import OAuthHandler, OAuthTokens, OAuthUserInfo


class YouTubeOAuthHandler(OAuthHandler):
    """
    YouTube OAuth 2.0 Handler

    Uses Google's OAuth 2.0 implementation
    Tokens are short-lived but include refresh tokens for long-term access

    Token Lifecycle:
    - Access tokens: Expire in 1 hour
    - Refresh tokens: Long-lived (until revoked)
    - Must request offline access to get refresh token
    """

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize YouTube OAuth handler

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth callback URL
        """
        super().__init__(client_id, client_secret, redirect_uri)

    def get_authorization_url(self, state: str = None) -> str:
        """
        Get authorization URL for user consent

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            URL to redirect user to for authorization
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join([
                "https://www.googleapis.com/auth/youtube.readonly",
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.force-ssl",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email"
            ]),
            "access_type": "offline",  # Request refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.AUTH_URL}?{query_string}"

    def exchange_code(self, code: str, **kwargs) -> OAuthTokens:
        """
        Exchange authorization code for access token and refresh token

        Args:
            code: Authorization code from callback

        Returns:
            OAuthTokens with access_token, refresh_token, and expiration
        """
        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        data = response.json()

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),  # Only provided on first auth
            expires_in=data.get("expires_in", 3600),
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope")
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Refresh token from initial authorization

        Returns:
            OAuthTokens with new access_token
        """
        response = requests.post(
            self.TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        data = response.json()

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=refresh_token,  # Refresh token stays the same
            expires_in=data.get("expires_in", 3600),
            token_type=data.get("token_type", "Bearer"),
            scope=data.get("scope")
        )

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get YouTube/Google user information

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with Google user ID and email
        """
        response = requests.get(
            self.USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()

        data = response.json()

        return OAuthUserInfo(
            platform_user_id=data["id"],
            username=data.get("name"),
            email=data.get("email"),
            profile_data=data
        )

    def get_channel_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get YouTube channel information for the authenticated user

        Args:
            access_token: OAuth access token

        Returns:
            Dict with channel ID, title, and other details
        """
        response = requests.get(
            f"{self.YOUTUBE_API_BASE}/channels",
            params={"part": "snippet,contentDetails,statistics", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("items"):
            raise ValueError("No YouTube channel found for this user")

        channel = data["items"][0]

        return {
            "id": channel["id"],
            "title": channel["snippet"]["title"],
            "description": channel["snippet"]["description"],
            "thumbnail": channel["snippet"]["thumbnails"]["default"]["url"],
            "subscriber_count": channel["statistics"].get("subscriberCount"),
            "video_count": channel["statistics"].get("videoCount"),
            "view_count": channel["statistics"].get("viewCount")
        }
