"""
OAuth Token Exchange
Exchanges authorization codes for access tokens from social platforms
"""
import requests
import logging
from typing import Dict, Optional
from urllib.parse import urlencode

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
    """Exchange Twitter OAuth 2.0 code for access token"""

    @staticmethod
    def exchange_code(
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code_verifier: str
    ) -> Dict:
        """
        Exchange authorization code for access token

        Args:
            code: Authorization code
            client_id: Twitter Client ID
            client_secret: Twitter Client Secret
            redirect_uri: OAuth redirect URI
            code_verifier: PKCE code verifier

        Returns:
            {
                "access_token": "...",
                "token_type": "bearer",
                "expires_in": 7200,
                "refresh_token": "...",
                "scope": "..."
            }
        """
        url = "https://api.twitter.com/2/oauth2/token"

        # Twitter requires Basic Auth
        auth = (client_id, client_secret)

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(url, auth=auth, data=data, headers=headers, timeout=10)
            response.raise_for_status()

            token_data = response.json()

            if "error" in token_data:
                error_msg = token_data.get("error_description", "Unknown error")
                logger.error(f"Twitter token exchange error: {error_msg}")
                raise TokenExchangeError(f"Twitter: {error_msg}")

            return token_data

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
