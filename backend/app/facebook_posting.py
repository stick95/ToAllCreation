"""
Facebook Posting Service
Handles posting videos/reels to Facebook Pages using Graph API v18.0
"""
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class FacebookPostingError(Exception):
    """Custom exception for Facebook posting errors"""
    pass

class FacebookPostingService:
    """Service for posting content to Facebook Pages"""

    GRAPH_API_VERSION = "v18.0"
    GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

    @staticmethod
    def post_reel(
        page_id: str,
        page_access_token: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a reel to a Facebook Page

        Args:
            page_id: Facebook Page ID
            page_access_token: Page-specific access token
            video_url: Publicly accessible URL to the video file
            caption: Optional caption for the reel

        Returns:
            Dict with post information including post_id

        Raises:
            FacebookPostingError: If posting fails
        """
        try:
            # Step 1: Initialize video upload
            init_url = f"{FacebookPostingService.GRAPH_API_BASE}/{page_id}/video_reels"

            init_params = {
                'access_token': page_access_token,
                'upload_phase': 'start'
            }

            logger.info(f"Initializing reel upload for page {page_id}")
            init_response = requests.post(init_url, params=init_params)

            if init_response.status_code != 200:
                error_data = init_response.json()
                logger.error(f"Failed to initialize upload: {error_data}")
                raise FacebookPostingError(f"Failed to initialize upload: {error_data.get('error', {}).get('message', 'Unknown error')}")

            init_data = init_response.json()
            video_id = init_data.get('video_id')

            if not video_id:
                raise FacebookPostingError("No video_id returned from initialization")

            logger.info(f"Upload initialized with video_id: {video_id}")

            # Step 2: Upload video file
            upload_url = f"{FacebookPostingService.GRAPH_API_BASE}/{video_id}"

            upload_params = {
                'access_token': page_access_token,
                'upload_phase': 'transfer',
                'video_file_chunk_start': 0,
                'upload_session_id': init_data.get('upload_session_id')
            }

            # Download video from URL and upload
            logger.info(f"Downloading video from {video_url}")
            video_response = requests.get(video_url, stream=True)

            if video_response.status_code != 200:
                raise FacebookPostingError(f"Failed to download video from URL: {video_url}")

            video_data = video_response.content

            logger.info(f"Uploading video ({len(video_data)} bytes)")
            upload_response = requests.post(
                upload_url,
                params=upload_params,
                files={'video_file_chunk': video_data}
            )

            if upload_response.status_code != 200:
                error_data = upload_response.json()
                logger.error(f"Failed to upload video: {error_data}")
                raise FacebookPostingError(f"Failed to upload video: {error_data.get('error', {}).get('message', 'Unknown error')}")

            logger.info("Video uploaded successfully")

            # Step 3: Finalize and publish
            publish_params = {
                'access_token': page_access_token,
                'upload_phase': 'finish',
                'video_state': 'PUBLISHED'
            }

            if caption:
                publish_params['description'] = caption

            logger.info(f"Publishing reel with video_id: {video_id}")
            publish_response = requests.post(upload_url, params=publish_params)

            if publish_response.status_code != 200:
                error_data = publish_response.json()
                logger.error(f"Failed to publish reel: {error_data}")
                raise FacebookPostingError(f"Failed to publish reel: {error_data.get('error', {}).get('message', 'Unknown error')}")

            publish_data = publish_response.json()

            logger.info(f"Reel published successfully: {publish_data}")
            logger.info(f"Full publish response - Status: {publish_response.status_code}, Data: {publish_data}")

            # Query the video to get its status
            status_url = f"{FacebookPostingService.GRAPH_API_BASE}/{video_id}"
            status_params = {
                'access_token': page_access_token,
                'fields': 'id,status,permalink_url'
            }

            status_response = requests.get(status_url, params=status_params)
            if status_response.status_code == 200:
                status_data = status_response.json()
                logger.info(f"Video status: {status_data}")

            return {
                'success': True,
                'video_id': video_id,
                'post_id': publish_data.get('id') or video_id,
                'platform': 'facebook',
                'page_id': page_id,
                'publish_response': publish_data
            }

        except FacebookPostingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error posting reel: {e}")
            raise FacebookPostingError(f"Unexpected error: {str(e)}")

    @staticmethod
    def post_video(
        page_id: str,
        page_access_token: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a regular video to a Facebook Page (fallback if reels fail)

        Args:
            page_id: Facebook Page ID
            page_access_token: Page-specific access token
            video_url: Publicly accessible URL to the video file
            caption: Optional caption for the video

        Returns:
            Dict with post information including post_id

        Raises:
            FacebookPostingError: If posting fails
        """
        try:
            url = f"{FacebookPostingService.GRAPH_API_BASE}/{page_id}/videos"

            params = {
                'access_token': page_access_token,
                'file_url': video_url
            }

            if caption:
                params['description'] = caption

            logger.info(f"Posting video to page {page_id}")
            response = requests.post(url, params=params)

            if response.status_code != 200:
                error_data = response.json()
                logger.error(f"Failed to post video: {error_data}")
                raise FacebookPostingError(f"Failed to post video: {error_data.get('error', {}).get('message', 'Unknown error')}")

            data = response.json()

            logger.info(f"Video posted successfully: {data}")

            return {
                'success': True,
                'video_id': data.get('id'),
                'post_id': data.get('id'),
                'platform': 'facebook',
                'page_id': page_id
            }

        except FacebookPostingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error posting video: {e}")
            raise FacebookPostingError(f"Unexpected error: {str(e)}")
