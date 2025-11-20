"""
OAuth Provider Configurations for Social Media Platforms
"""
import os
from typing import Dict, Optional
from urllib.parse import urlencode


class OAuthProvider:
    """Base OAuth provider configuration"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self, state: str) -> str:
        """Generate OAuth authorization URL"""
        raise NotImplementedError

    def get_scopes(self) -> list:
        """Get required OAuth scopes"""
        raise NotImplementedError


class FacebookProvider(OAuthProvider):
    """Facebook/Instagram OAuth Provider (uses same Meta Graph API)"""

    AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
    API_URL = "https://graph.facebook.com/v18.0"

    def get_scopes(self) -> list:
        return [
            "pages_show_list",  # List pages user manages
            "pages_manage_posts",  # Post to Facebook pages
            "pages_read_engagement",  # Read page data
            "instagram_basic",  # Instagram access
            "instagram_content_publish",  # Post to Instagram
            "business_management",  # Access to business assets
            "public_profile",  # Basic profile
        ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": ",".join(self.get_scopes()),
            "response_type": "code",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"


class TwitterProvider(OAuthProvider):
    """X (Twitter) OAuth 2.0 Provider"""

    AUTH_URL = "https://twitter.com/i/oauth2/authorize"
    TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
    API_URL = "https://api.twitter.com/2"

    def get_scopes(self) -> list:
        return [
            "tweet.read",
            "tweet.write",
            "users.read",
            "offline.access",  # For refresh token
        ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(self.get_scopes()),
            "response_type": "code",
            "code_challenge": "challenge",  # PKCE required
            "code_challenge_method": "plain",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"


class LinkedInProvider(OAuthProvider):
    """LinkedIn OAuth 2.0 Provider"""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_URL = "https://api.linkedin.com/v2"

    def get_scopes(self) -> list:
        return [
            "w_member_social",  # Post on behalf of user
            "w_organization_social",  # Post to organization pages
            "r_liteprofile",  # Read profile
            "r_basicprofile",  # Basic profile
            "r_organization_social",  # Read organization info
        ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": " ".join(self.get_scopes()),
            "response_type": "code",
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"


class OAuthProviderFactory:
    """Factory to create OAuth provider instances"""

    @staticmethod
    def create_provider(platform: str, redirect_uri: str) -> Optional[OAuthProvider]:
        """
        Create OAuth provider instance for platform

        Environment variables required:
        - FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET
        - TWITTER_CLIENT_ID, TWITTER_CLIENT_SECRET
        - LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET
        """
        platform = platform.lower()

        if platform in ["facebook", "instagram"]:
            client_id = os.environ.get("FACEBOOK_CLIENT_ID")
            client_secret = os.environ.get("FACEBOOK_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("Facebook OAuth credentials not configured")
            return FacebookProvider(client_id, client_secret, redirect_uri)

        elif platform == "twitter":
            client_id = os.environ.get("TWITTER_CLIENT_ID")
            client_secret = os.environ.get("TWITTER_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("Twitter OAuth credentials not configured")
            return TwitterProvider(client_id, client_secret, redirect_uri)

        elif platform == "linkedin":
            client_id = os.environ.get("LINKEDIN_CLIENT_ID")
            client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("LinkedIn OAuth credentials not configured")
            return LinkedInProvider(client_id, client_secret, redirect_uri)

        else:
            raise ValueError(f"Unsupported platform: {platform}")


def get_oauth_url(platform: str, redirect_uri: str, state: str) -> str:
    """
    Generate OAuth authorization URL for a platform

    Args:
        platform: Social media platform (facebook, twitter, linkedin, instagram)
        redirect_uri: OAuth callback URL
        state: CSRF protection state token

    Returns:
        Authorization URL to redirect user to
    """
    provider = OAuthProviderFactory.create_provider(platform, redirect_uri)
    return provider.get_authorization_url(state)
