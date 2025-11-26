"""
Facebook/Instagram OAuth Handler
Handles OAuth for both Facebook Pages and Instagram Business accounts
"""
import requests
from typing import Dict, Any, Optional
from .base_handler import OAuthHandler, OAuthTokens, OAuthUserInfo


class FacebookOAuthHandler(OAuthHandler):
    """
    Facebook OAuth 2.0 Handler

    Also handles Instagram Business accounts (linked to Facebook Pages)

    Token Lifecycle:
    - Short-lived tokens: 1 hour
    - Long-lived tokens: 60 days
    - Page tokens: Never expire (but should be refreshed)
    """

    GRAPH_API_BASE = "https://graph.facebook.com/v18.0"

    def exchange_code(self, code: str, **kwargs) -> OAuthTokens:
        """
        Exchange authorization code for access token
        Then exchange for long-lived token (60 days)

        Args:
            code: Authorization code from OAuth callback

        Returns:
            OAuthTokens with long-lived access token (60 days)
        """
        # Step 1: Exchange code for short-lived token
        token_url = f"{self.GRAPH_API_BASE}/oauth/access_token"

        response = requests.get(token_url, params={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        })
        response.raise_for_status()

        short_lived = response.json()

        # Step 2: Exchange for long-lived token (60 days)
        long_lived = self._get_long_lived_token(short_lived["access_token"])

        return OAuthTokens(
            access_token=long_lived["access_token"],
            refresh_token=None,  # Facebook doesn't use refresh tokens
            expires_in=long_lived.get("expires_in", 5184000),  # 60 days default
            token_type="Bearer"
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh Facebook access token

        Note: Facebook doesn't use refresh tokens like other platforms.
        Instead, we exchange the current access token for a new long-lived token.

        Args:
            refresh_token: Current access token (Facebook doesn't have separate refresh tokens)

        Returns:
            OAuthTokens with new access token
        """
        long_lived = self._get_long_lived_token(refresh_token)

        return OAuthTokens(
            access_token=long_lived["access_token"],
            refresh_token=None,
            expires_in=long_lived.get("expires_in", 5184000),
            token_type="Bearer"
        )

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get Facebook user information

        Args:
            access_token: Valid Facebook access token

        Returns:
            OAuthUserInfo with Facebook user ID and name
        """
        me_url = f"{self.GRAPH_API_BASE}/me"

        response = requests.get(me_url, params={
            "access_token": access_token,
            "fields": "id,name,email"
        })
        response.raise_for_status()

        data = response.json()

        return OAuthUserInfo(
            platform_user_id=data["id"],
            username=data.get("name"),
            email=data.get("email"),
            profile_data=data
        )

    def get_pages(self, access_token: str) -> list:
        """
        Get Facebook Pages that the user manages

        Args:
            access_token: User's Facebook access token

        Returns:
            List of pages with id, name, access_token, category
        """
        pages_url = f"{self.GRAPH_API_BASE}/me/accounts"

        response = requests.get(pages_url, params={
            "access_token": access_token
        })
        response.raise_for_status()

        data = response.json()
        return data.get("data", [])

    def get_instagram_accounts(self, access_token: str) -> list:
        """
        Get Instagram Business accounts linked to Facebook Pages

        Args:
            access_token: User's Facebook access token

        Returns:
            List of Instagram Business accounts
        """
        # First get Facebook Pages
        pages = self.get_pages(access_token)

        instagram_accounts = []

        for page in pages:
            page_id = page["id"]
            page_token = page.get("access_token", access_token)

            # Check if page has linked Instagram account
            ig_url = f"{self.GRAPH_API_BASE}/{page_id}"

            response = requests.get(ig_url, params={
                "access_token": page_token,
                "fields": "instagram_business_account"
            })

            if response.ok:
                data = response.json()
                if "instagram_business_account" in data:
                    ig_id = data["instagram_business_account"]["id"]

                    # Get Instagram account details
                    ig_details_url = f"{self.GRAPH_API_BASE}/{ig_id}"
                    ig_response = requests.get(ig_details_url, params={
                        "access_token": page_token,
                        "fields": "username,name,profile_picture_url"
                    })

                    if ig_response.ok:
                        ig_data = ig_response.json()
                        ig_data["page_id"] = page_id
                        ig_data["access_token"] = page_token
                        instagram_accounts.append(ig_data)

        return instagram_accounts

    def _get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """
        Exchange short-lived token for long-lived token (60 days)

        Args:
            short_lived_token: Short-lived access token

        Returns:
            Dict with access_token and expires_in
        """
        exchange_url = f"{self.GRAPH_API_BASE}/oauth/access_token"

        response = requests.get(exchange_url, params={
            "grant_type": "fb_exchange_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "fb_exchange_token": short_lived_token
        })
        response.raise_for_status()

        return response.json()
