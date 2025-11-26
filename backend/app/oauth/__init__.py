"""
OAuth Handler Classes
Handles OAuth flows for different social media platforms
"""
from .base_handler import OAuthHandler
from .facebook_handler import FacebookOAuthHandler

__all__ = [
    'OAuthHandler',
    'FacebookOAuthHandler',
]

# TODO: Import additional handlers as they are implemented:
# from .twitter_handler import TwitterOAuthHandler
# from .youtube_handler import YouTubeOAuthHandler
# from .linkedin_handler import LinkedInOAuthHandler
# from .tiktok_handler import TikTokOAuthHandler
