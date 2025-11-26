"""
OAuth Handler Classes
Handles OAuth flows for different social media platforms
"""
from .base_handler import OAuthHandler
from .facebook_handler import FacebookOAuthHandler
from .twitter_handler import TwitterOAuthHandler
from .youtube_handler import YouTubeOAuthHandler
from .linkedin_handler import LinkedInOAuthHandler
from .tiktok_handler import TikTokOAuthHandler

__all__ = [
    'OAuthHandler',
    'FacebookOAuthHandler',
    'TwitterOAuthHandler',
    'YouTubeOAuthHandler',
    'LinkedInOAuthHandler',
    'TikTokOAuthHandler',
]
