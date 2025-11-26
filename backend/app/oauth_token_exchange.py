"""
OAuth Token Exchange
Exchanges authorization codes for access tokens from social platforms
"""
import requests
import logging
import time
import hmac
import hashlib
import base64
import secrets
from typing import Dict, Optional
from urllib.parse import urlencode, quote

logger = logging.getLogger(__name__)


class TokenExchangeError(Exception):
    """Error during token exchange"""
    pass


class FacebookTokenExchange:
    """Exchange Facebook OAuth code for access token"""

    @staticmethod
    def exchange_code(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code from OAuth callback
            client_id: Facebook App ID
            client_secret: Facebook App Secret
            redirect_uri: OAuth redirect URI (must match what was used in authorization)

        Returns:
            {
                "access_token": "...",
                "token_type": "bearer",
                "expires_in": 5183944  # seconds
            }

        Raises:
            TokenExchangeError: If exchange fails
        """
        url = "https://graph.facebook.com/v18.0/oauth/access_token"

        params = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"Facebook token exchange error: {error_msg}")
                raise TokenExchangeError(f"Facebook: {error_msg}")

            return {
                "access_token": data["access_token"],
                "token_type": data.get("token_type", "bearer"),
                "expires_in": data.get("expires_in", 5184000)  # ~60 days default
            }

        except requests.RequestException as e:
            logger.error(f"Facebook token exchange request failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")

    @staticmethod
    def get_long_lived_token(short_lived_token: str, client_id: str, client_secret: str) -> Dict:
        """
        Exchange short-lived token for long-lived token (60 days)

        Args:
            short_lived_token: Access token from initial exchange
            client_id: Facebook App ID
            client_secret: Facebook App Secret

        Returns:
            {
                "access_token": "...",
                "token_type": "bearer",
                "expires_in": 5183944
            }
        """
        url = "https://graph.facebook.com/v18.0/oauth/access_token"

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "fb_exchange_token": short_lived_token
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"Long-lived token exchange error: {error_msg}")
                raise TokenExchangeError(f"Facebook: {error_msg}")

            return {
                "access_token": data["access_token"],
                "token_type": data.get("token_type", "bearer"),
                "expires_in": data.get("expires_in", 5184000)
            }

        except requests.RequestException as e:
            logger.error(f"Long-lived token exchange failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")


class TwitterTokenExchange:
    """Exchange Twitter OAuth 1.0a tokens for access token"""

    @staticmethod
    def _generate_oauth1a_signature(
        method: str,
        url: str,
        params: Dict[str, str],
        api_secret: str,
        token_secret: str
    ) -> str:
        """
        Generate OAuth 1.0a signature

        Args:
            method: HTTP method (POST, GET)
            url: Full URL
            params: OAuth parameters
            api_secret: API Secret (consumer secret)
            token_secret: OAuth token secret

        Returns:
            Base64-encoded HMAC-SHA1 signature
        """
        # Sort parameters
        sorted_params = sorted(params.items())
        param_string = '&'.join([f'{quote(str(k), safe="")}={quote(str(v), safe="")}' for k, v in sorted_params])

        # Create signature base string
        signature_base = f'{method.upper()}&{quote(url, safe="")}&{quote(param_string, safe="")}'

        # Create signing key
        signing_key = f'{quote(api_secret, safe="")}&{quote(token_secret, safe="")}'

        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode(),
                signature_base.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        return signature

    @staticmethod
    def exchange_code(
        oauth_token: str,
        oauth_verifier: str,
        oauth_token_secret: str,
        api_key: str,
        api_secret: str
    ) -> Dict:
        """
        Exchange OAuth 1.0a request token for access token

        Args:
            oauth_token: OAuth token from authorization callback
            oauth_verifier: OAuth verifier from authorization callback
            oauth_token_secret: OAuth token secret from request token step
            api_key: Twitter API Key (consumer key)
            api_secret: Twitter API Secret (consumer secret)

        Returns:
            {
                "access_token": "...",
                "access_token_secret": "...",
                "user_id": "...",
                "screen_name": "..."
            }
        """
        url = "https://api.twitter.com/oauth/access_token"

        # OAuth parameters
        oauth_nonce = secrets.token_hex(16)
        oauth_timestamp = str(int(time.time()))

        oauth_params = {
            'oauth_consumer_key': api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': oauth_token,
            'oauth_verifier': oauth_verifier,
            'oauth_version': '1.0'
        }

        # Generate signature
        signature = TwitterTokenExchange._generate_oauth1a_signature(
            method='POST',
            url=url,
            params=oauth_params,
            api_secret=api_secret,
            token_secret=oauth_token_secret
        )

        oauth_params['oauth_signature'] = signature

        # Build Authorization header
        auth_header = 'OAuth ' + ', '.join([f'{quote(k, safe="")}="{quote(v, safe="")}"' for k, v in sorted(oauth_params.items())])

        headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            response = requests.post(url, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"Twitter access token exchange failed: {response.text}")
                raise TokenExchangeError(f"Twitter: {response.text}")

            # Parse response (format: oauth_token=xxx&oauth_token_secret=yyy&user_id=zzz&screen_name=www)
            response_params = dict(param.split('=') for param in response.text.split('&'))

            access_token = response_params.get('oauth_token')
            access_token_secret = response_params.get('oauth_token_secret')
            user_id = response_params.get('user_id')
            screen_name = response_params.get('screen_name')

            if not access_token or not access_token_secret:
                raise TokenExchangeError("Invalid response from Twitter access token endpoint")

            return {
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "user_id": user_id,
                "screen_name": screen_name
            }

        except requests.RequestException as e:
            logger.error(f"Twitter token exchange failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")


class LinkedInTokenExchange:
    """Exchange LinkedIn OAuth code for access token"""

    @staticmethod
    def exchange_code(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_id: LinkedIn Client ID
            client_secret: LinkedIn Client Secret
            redirect_uri: OAuth redirect URI

        Returns:
            {
                "access_token": "...",
                "expires_in": 5184000,  # 60 days
                "refresh_token": "...",
                "refresh_token_expires_in": 31536000  # 365 days
            }
        """
        url = "https://www.linkedin.com/oauth/v2/accessToken"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", "Unknown error")
                logger.error(f"LinkedIn token exchange error: {error_msg}")
                raise TokenExchangeError(f"LinkedIn: {error_msg}")

            return token_data

        except requests.RequestException as e:
            logger.error(f"LinkedIn token exchange failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")


class YouTubeTokenExchange:
    """Exchange YouTube (Google) OAuth code for access token"""

    @staticmethod
    def exchange_code(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_id: YouTube (Google) Client ID
            client_secret: YouTube (Google) Client Secret
            redirect_uri: OAuth redirect URI

        Returns:
            {
                "access_token": "...",
                "expires_in": 3600,  # 1 hour
                "refresh_token": "...",
                "scope": "...",
                "token_type": "Bearer"
            }
        """
        url = "https://oauth2.googleapis.com/token"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", "Unknown error")
                logger.error(f"YouTube token exchange error: {error_msg}")
                raise TokenExchangeError(f"YouTube: {error_msg}")

            return token_data

        except requests.RequestException as e:
            logger.error(f"YouTube token exchange failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")

    @staticmethod
    def refresh_token(
        refresh_token: str,
        client_id: str,
        client_secret: str
    ) -> Dict:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token
            client_id: YouTube (Google) Client ID
            client_secret: YouTube (Google) Client Secret

        Returns:
            {
                "access_token": "...",
                "expires_in": 3600,
                "scope": "...",
                "token_type": "Bearer"
            }
        """
        url = "https://oauth2.googleapis.com/token"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", "Unknown error")
                logger.error(f"YouTube token refresh error: {error_msg}")
                raise TokenExchangeError(f"YouTube: {error_msg}")

            return token_data

        except requests.RequestException as e:
            logger.error(f"YouTube token refresh failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")


class TikTokTokenExchange:
    """Exchange TikTok OAuth code for access token"""

    @staticmethod
    def exchange_code(
        code: str,
        client_key: str,
        client_secret: str,
        redirect_uri: str
    ) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_key: TikTok Client Key (note: TikTok uses client_key instead of client_id)
            client_secret: TikTok Client Secret
            redirect_uri: OAuth redirect URI

        Returns:
            {
                "access_token": "...",
                "expires_in": 86400,  # 24 hours
                "refresh_token": "...",
                "refresh_expires_in": 31536000,  # 365 days
                "open_id": "...",
                "scope": "...",
                "token_type": "Bearer"
            }
        """
        url = "https://open.tiktokapis.com/v2/oauth/token/"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_key": client_key,
            "client_secret": client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", token_data.get("error", "Unknown error"))
                logger.error(f"TikTok token exchange error: {error_msg}")
                raise TokenExchangeError(f"TikTok: {error_msg}")

            return token_data

        except requests.RequestException as e:
            logger.error(f"TikTok token exchange failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")

    @staticmethod
    def refresh_token(
        refresh_token: str,
        client_key: str,
        client_secret: str
    ) -> Dict:
        """
        Refresh access token using refresh token

        Args:
            refresh_token: Refresh token
            client_key: TikTok Client Key
            client_secret: TikTok Client Secret

        Returns:
            {
                "access_token": "...",
                "expires_in": 86400,
                "refresh_token": "...",
                "refresh_expires_in": 31536000,
                "open_id": "...",
                "scope": "...",
                "token_type": "Bearer"
            }
        """
        url = "https://open.tiktokapis.com/v2/oauth/token/"

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_key": client_key,
            "client_secret": client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", token_data.get("error", "Unknown error"))
                logger.error(f"TikTok token refresh error: {error_msg}")
                raise TokenExchangeError(f"TikTok: {error_msg}")

            return token_data

        except requests.RequestException as e:
            logger.error(f"TikTok token refresh failed: {e}")
            raise TokenExchangeError(f"Network error: {str(e)}")
