"""
LinkedIn OAuth Handler
Handles OAuth 2.0 for LinkedIn
"""
import requests
from typing import Dict, Any
from .base_handler import OAuthHandler, OAuthTokens, OAuthUserInfo


class LinkedInOAuthHandler(OAuthHandler):
    """
    LinkedIn OAuth 2.0 Handler

    Token Lifecycle:
    - Access tokens: Expire in 60 days
    - Refresh tokens: Available for extended access
    - LinkedIn API v2 is used for all operations
    """

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    API_BASE = "https://api.linkedin.com/v2"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize LinkedIn OAuth handler

        Args:
            client_id: LinkedIn app client ID
            client_secret: LinkedIn app client secret
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
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join([
                "openid",
                "profile",
                "email",
                "w_member_social"
            ])
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
            OAuthTokens with access_token and expiration (60 days)
        """
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        data = response.json()

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_in=data.get("expires_in", 5184000),  # 60 days default
            token_type="Bearer",
            scope=data.get("scope")
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Refresh expired access token using refresh token

        Args:
            refresh_token: Refresh token from initial authorization

        Returns:
            OAuthTokens with new access_token

        Note:
            LinkedIn tokens are long-lived (60 days) but can be refreshed
        """
        response = requests.post(
            self.TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        data = response.json()

        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            expires_in=data.get("expires_in", 5184000),
            token_type="Bearer",
            scope=data.get("scope")
        )

    def get_user_info(self, access_token: str) -> OAuthUserInfo:
        """
        Get LinkedIn user profile information using OpenID Connect

        Args:
            access_token: OAuth access token

        Returns:
            OAuthUserInfo with LinkedIn user ID and profile data
        """
        # Use OpenID Connect userinfo endpoint (modern LinkedIn API)
        userinfo_url = "https://api.linkedin.com/v2/userinfo"
        profile_response = requests.get(
            userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        # OpenID Connect userinfo provides: sub, name, given_name, family_name, picture, email
        return OAuthUserInfo(
            platform_user_id=profile_data.get("sub"),  # LinkedIn user ID
            username=profile_data.get("name"),
            email=profile_data.get("email"),
            profile_data=profile_data
        )

    def get_organization_pages(self, access_token: str) -> list:
        """
        Get organization pages the user can manage

        Args:
            access_token: OAuth access token

        Returns:
            List of organization pages with their IDs and names
        """
        response = requests.get(
            f"{self.API_BASE}/organizationalEntityAcls?q=roleAssignee",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()

        data = response.json()
        organizations = []

        for element in data.get("elements", []):
            org_urn = element.get("organizationalTarget")
            if org_urn:
                # Extract organization ID from URN
                org_id = org_urn.split(":")[-1]

                # Get organization details
                org_response = requests.get(
                    f"{self.API_BASE}/organizations/{org_id}",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

                if org_response.status_code == 200:
                    org_data = org_response.json()
                    organizations.append({
                        "id": org_id,
                        "name": org_data.get("localizedName"),
                        "vanity_name": org_data.get("vanityName"),
                        "logo_url": org_data.get("logoV2", {}).get("original")
                    })

        return organizations
