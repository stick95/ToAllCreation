"""
Base OAuth Handler
Abstract base class for all OAuth platform handlers
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class OAuthTokens:
    """OAuth token data"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"
    scope: Optional[str] = None


@dataclass
class OAuthUserInfo:
    """Platform user information"""
    platform_user_id: str
    username: Optional[str] = None
    email: Optional[str] = None
    profile_data: Optional[Dict[str, Any]] = None


class OAuthHandler(ABC):
    """
    Abstract base class for OAuth handlers

    Each platform implements:
    - Token exchange (code → access token)
    - Token refresh (refresh token → new access token)
    - User info retrieval
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    def exchange_code(self, code: str, **kwargs) -> OAuthTokens:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            **kwargs: Platform-specific parameters

        Returns:
            OAuthTokens with access_token, refresh_token, expires_in
        """
        pass

    @abstractmethod
    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh an expired access token

        Args:
            refresh_token: The refresh token

        Returns:
            OAuthTokens with new access_token
        """
        pass

    @abstractmethod
    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get platform user information

        Args:
            access_token: Valid access token

        Returns:
            OAuthUserInfo with platform_user_id, username, etc.
        """
        pass

    def should_refresh_token(self, token_expires_at: Optional[int]) -> bool:
        """
        Check if token should be refreshed

        Args:
            token_expires_at: Unix timestamp when token expires

        Returns:
            True if token should be refreshed (expires in < 5 minutes)
        """
        if not token_expires_at:
            return False

        import time
        buffer_seconds = 300  # 5 minutes
        return time.time() >= (token_expires_at - buffer_seconds)
