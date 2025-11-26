"""
OAuth Provider Configurations for Social Media Platforms
"""
import os
import time
import hmac
import hashlib
import base64
import secrets
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, quote


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
    """X (Twitter) OAuth 1.0a Provider"""

    # OAuth 1.0a endpoints
    REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
    AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
    ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
    API_URL = "https://api.twitter.com/2"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Twitter OAuth 1.0a provider

        Note: For Twitter OAuth 1.0a:
        - client_id is the API Key (consumer key)
        - client_secret is the API Secret (consumer secret)
        """
        super().__init__(client_id, client_secret, redirect_uri)
        self.api_key = client_id  # Alias for clarity
        self.api_secret = client_secret  # Alias for clarity

    def get_scopes(self) -> list:
        """OAuth 1.0a doesn't use scopes in the same way as OAuth 2.0"""
        return []

    def _generate_oauth1a_signature(
        self,
        method: str,
        url: str,
        params: Dict[str, str],
        token_secret: str = ""
    ) -> str:
        """
        Generate OAuth 1.0a signature

        Args:
            method: HTTP method (POST, GET)
            url: Full URL
            params: OAuth parameters
            token_secret: Token secret (empty for request token)

        Returns:
            Base64-encoded HMAC-SHA1 signature
        """
        # Sort parameters
        sorted_params = sorted(params.items())
        param_string = '&'.join([f'{quote(str(k), safe="")}={quote(str(v), safe="")}' for k, v in sorted_params])

        # Create signature base string
        signature_base = f'{method.upper()}&{quote(url, safe="")}&{quote(param_string, safe="")}'

        # Create signing key
        signing_key = f'{quote(self.api_secret, safe="")}&{quote(token_secret, safe="")}'

        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode(),
                signature_base.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        return signature

    def get_request_token(self, state: str) -> Tuple[str, str]:
        """
        Step 1 of OAuth 1.0a: Get request token

        Args:
            state: CSRF protection state (stored for callback verification)

        Returns:
            Tuple of (oauth_token, oauth_token_secret)
        """
        # OAuth parameters for request token
        oauth_nonce = secrets.token_hex(16)
        oauth_timestamp = str(int(time.time()))

        oauth_params = {
            'oauth_callback': self.redirect_uri,
            'oauth_consumer_key': self.api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_version': '1.0'
        }

        # Generate signature
        signature = self._generate_oauth1a_signature(
            method='POST',
            url=self.REQUEST_TOKEN_URL,
            params=oauth_params,
            token_secret=''  # Empty for request token
        )

        oauth_params['oauth_signature'] = signature

        # Build Authorization header
        auth_header = 'OAuth ' + ', '.join([f'{quote(k, safe="")}="{quote(v, safe="")}"' for k, v in sorted(oauth_params.items())])

        # Make request to get request token
        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(self.REQUEST_TOKEN_URL, headers=headers, timeout=30)

        if response.status_code != 200:
            raise Exception(f"Failed to get request token: {response.text}")

        # Parse response (format: oauth_token=xxx&oauth_token_secret=yyy&oauth_callback_confirmed=true)
        response_params = dict(param.split('=') for param in response.text.split('&'))

        oauth_token = response_params.get('oauth_token')
        oauth_token_secret = response_params.get('oauth_token_secret')

        if not oauth_token or not oauth_token_secret:
            raise Exception("Invalid response from Twitter request token endpoint")

        return oauth_token, oauth_token_secret

    def get_authorization_url(self, state: str) -> str:
        """
        Generate OAuth 1.0a authorization URL

        This is a two-step process:
        1. Get request token from Twitter
        2. Build authorization URL with the request token

        Args:
            state: CSRF protection state token

        Returns:
            Authorization URL with oauth_token
        """
        # Step 1: Get request token
        oauth_token, oauth_token_secret = self.get_request_token(state)

        # Store oauth_token_secret temporarily (needs to be retrieved in callback)
        # We'll return it as part of a special format that the caller can parse
        # Format: URL|oauth_token_secret
        # The caller should store oauth_token_secret with the state for retrieval in callback

        # Step 2: Build authorization URL
        params = {
            'oauth_token': oauth_token
        }

        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"

        # Return URL and token_secret as tuple (caller must handle this)
        return auth_url, oauth_token_secret


class LinkedInProvider(OAuthProvider):
    """LinkedIn OAuth 2.0 Provider"""

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_URL = "https://api.linkedin.com/v2"

    def get_scopes(self) -> list:
        return [
            "openid",  # OpenID Connect (required)
            "profile",  # Basic profile information
            "email",  # Email address
            "w_member_social",  # Post on behalf of user (personal)
            # "w_organization_social",  # Post to organization pages (requires Community Management API)
            # "r_organization_social",  # Read organization info (requires Community Management API)
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


class YouTubeProvider(OAuthProvider):
    """YouTube (Google) OAuth 2.0 Provider"""

    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def get_scopes(self) -> list:
        return [
            "https://www.googleapis.com/auth/youtube.upload",  # Upload videos
            "https://www.googleapis.com/auth/youtube.readonly",  # Read channel info
        ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.get_scopes()),
            "state": state,
            "access_type": "offline",  # Get refresh token
            "prompt": "consent"  # Force consent to get refresh token
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"


class TikTokProvider(OAuthProvider):
    """TikTok OAuth 2.0 Provider"""

    AUTH_URL = "https://www.tiktok.com/v2/auth/authorize"
    TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"

    def get_scopes(self) -> list:
        # Include video posting scopes for Content Posting API
        return [
            "user.info.basic",  # Basic user info (default scope, always available)
            "video.upload",  # Upload video content
            "video.publish",  # Publish video posts
        ]

    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_key": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": ",".join(self.get_scopes()),
            "state": state,
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
            # For OAuth 1.0a, we use API Key/Secret instead of Client ID/Secret
            api_key = os.environ.get("TWITTER_API_KEY")
            api_secret = os.environ.get("TWITTER_API_SECRET")
            if not api_key or not api_secret:
                raise ValueError("Twitter OAuth credentials not configured")
            return TwitterProvider(api_key, api_secret, redirect_uri)

        elif platform == "linkedin":
            client_id = os.environ.get("LINKEDIN_CLIENT_ID")
            client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("LinkedIn OAuth credentials not configured")
            return LinkedInProvider(client_id, client_secret, redirect_uri)

        elif platform == "youtube":
            client_id = os.environ.get("YOUTUBE_CLIENT_ID")
            # YouTube client secret is stored in SSM Parameter Store (SecureString)
            from ssm_helper import get_youtube_client_secret
            client_secret = get_youtube_client_secret()
            if not client_id or not client_secret:
                raise ValueError("YouTube OAuth credentials not configured")
            return YouTubeProvider(client_id, client_secret, redirect_uri)

        elif platform == "tiktok":
            client_id = os.environ.get("TIKTOK_CLIENT_ID")
            client_secret = os.environ.get("TIKTOK_CLIENT_SECRET")
            if not client_id or not client_secret:
                raise ValueError("TikTok OAuth credentials not configured")
            return TikTokProvider(client_id, client_secret, redirect_uri)

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
