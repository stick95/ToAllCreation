"""
Twitter OAuth Handler
Handles OAuth 1.0a for Twitter/X
"""
import requests
from typing import Dict, Any
from requests_oauthlib import OAuth1
from .base_handler import OAuthHandler, OAuthTokens, OAuthUserInfo


class TwitterOAuthHandler(OAuthHandler):
    """
    Twitter OAuth 1.0a Handler

    Note: Twitter uses OAuth 1.0a, not OAuth 2.0
    Tokens do not expire, but require both access_token and access_token_secret

    Token Lifecycle:
    - Request tokens: Short-lived, used for authorization
    - Access tokens: Never expire (but can be revoked)
    - No refresh token mechanism
    """

    REQUEST_TOKEN_URL = "https://api.twitter.com/oauth/request_token"
    AUTHORIZE_URL = "https://api.twitter.com/oauth/authorize"
    ACCESS_TOKEN_URL = "https://api.twitter.com/oauth/access_token"
    API_BASE = "https://api.twitter.com/1.1"

    def __init__(self, api_key: str, api_secret: str, callback_url: str):
        """
        Initialize Twitter OAuth handler

        Args:
            api_key: Twitter API key (client_id equivalent)
            api_secret: Twitter API secret (client_secret equivalent)
            callback_url: OAuth callback URL
        """
        # Twitter uses different terminology than OAuth 2.0
        super().__init__(api_key, api_secret, callback_url)
        self.api_key = api_key
        self.api_secret = api_secret
        self.callback_url = callback_url

    def get_request_token(self) -> Dict[str, str]:
        """
        Step 1: Obtain request token

        Returns:
            Dict with oauth_token and oauth_token_secret
        """
        oauth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            callback_uri=self.callback_url
        )

        response = requests.post(self.REQUEST_TOKEN_URL, auth=oauth)
        response.raise_for_status()

        credentials = dict(x.split('=') for x in response.text.split('&'))
        return credentials

    def get_authorization_url(self, oauth_token: str) -> str:
        """
        Step 2: Get authorization URL for user

        Args:
            oauth_token: Request token from get_request_token()

        Returns:
            URL to redirect user to for authorization
        """
        return f"{self.AUTHORIZE_URL}?oauth_token={oauth_token}"

    def exchange_code(self, oauth_token: str, oauth_verifier: str, oauth_token_secret: str, **kwargs) -> OAuthTokens:
        """
        Step 3: Exchange request token for access token

        Args:
            oauth_token: OAuth token from callback
            oauth_verifier: OAuth verifier from callback
            oauth_token_secret: Token secret from get_request_token()

        Returns:
            OAuthTokens with access_token and refresh_token (which stores access_token_secret)
        """
        oauth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier
        )

        response = requests.post(self.ACCESS_TOKEN_URL, auth=oauth)
        response.raise_for_status()

        credentials = dict(x.split('=') for x in response.text.split('&'))

        return OAuthTokens(
            access_token=credentials['oauth_token'],
            refresh_token=credentials['oauth_token_secret'],  # Store secret in refresh_token field
            expires_in=None,  # OAuth 1.0a tokens don't expire
            token_type="OAuth1.0a"
        )

    def refresh_access_token(self, refresh_token: str) -> OAuthTokens:
        """
        Twitter OAuth 1.0a tokens don't expire or refresh

        Args:
            refresh_token: Not used for Twitter

        Returns:
            Raises NotImplementedError as Twitter tokens don't refresh
        """
        raise NotImplementedError(
            "Twitter OAuth 1.0a tokens do not expire and cannot be refreshed. "
            "Use the existing access_token and access_token_secret."
        )

    def get_user_info(self, access_token: str, access_token_secret: str = None) -> OAuthUserInfo:
        """
        Get Twitter user information

        Args:
            access_token: OAuth access token
            access_token_secret: OAuth access token secret (required for OAuth 1.0a)

        Returns:
            OAuthUserInfo with Twitter user ID and username
        """
        if not access_token_secret:
            raise ValueError("access_token_secret is required for Twitter OAuth 1.0a")

        oauth = OAuth1(
            self.api_key,
            client_secret=self.api_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret
        )

        verify_url = f"{self.API_BASE}/account/verify_credentials.json"
        response = requests.get(verify_url, auth=oauth)
        response.raise_for_status()

        data = response.json()

        return OAuthUserInfo(
            platform_user_id=str(data["id"]),
            username=data.get("screen_name"),
            email=data.get("email"),  # May be None if not requested in scope
            profile_data=data
        )
