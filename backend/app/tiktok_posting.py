"""
TikTok Posting Service
Handles posting videos to TikTok using their Content Posting API
"""
import requests
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TikTokPostingError(Exception):
    """Custom exception for TikTok posting errors"""
    pass


class TikTokPostingService:
    """Service for posting videos to TikTok"""

    # Using Direct Post API for direct upload
    API_BASE = "https://open.tiktokapis.com/v2/"

    @staticmethod
    def post_video(
        open_id: str,
        access_token: str,
        video_url: str,
        caption: str
    ) -> Dict[str, Any]:
        """
        Post a video to TikTok using Content Posting API

        Args:
            open_id: TikTok user's open_id
            access_token: TikTok access token
            video_url: Public URL to the video file
            caption: Post caption/text (max 2200 characters)

        Returns:
            Dict containing publish_id and status
        """
        try:
            logger.info(f"Starting TikTok video post for user {open_id}")

            # Step 1: Download video from S3 first to get size
            logger.info("Step 1: Downloading video from S3")
            video_response = requests.get(video_url, timeout=120)  # Increased to 2 minutes
            video_response.raise_for_status()
            video_data = video_response.content
            video_size = len(video_data)
            logger.info(f"Downloaded {video_size} bytes ({video_size / 1024 / 1024:.2f} MB)")

            # Step 2: Initialize video upload with size info
            logger.info("Step 2: Initializing video upload with TikTok")
            init_response = TikTokPostingService._initialize_upload(
                open_id, access_token, video_size, caption
            )

            logger.info(f"Init response: {init_response}")

            # Extract upload URL and publish ID
            data = init_response.get("data", {})
            publish_id = data.get("publish_id")
            upload_url = data.get("upload_url")

            if not publish_id or not upload_url:
                raise TikTokPostingError(f"Invalid init response: {init_response}")

            logger.info(f"Publish ID: {publish_id}")
            logger.info(f"Upload URL received")

            # Step 3: Upload video to TikTok
            logger.info("Step 3: Uploading video to TikTok")
            TikTokPostingService._upload_video(upload_url, video_data)

            # Step 4: Check publish status
            logger.info("Step 4: Checking publish status")
            publish_result = TikTokPostingService._publish_video(
                open_id, publish_id, caption, access_token
            )

            logger.info(f"TikTok video published successfully: {publish_result}")

            return {
                'platform': 'tiktok',
                'publish_id': publish_id,
                'status': 'success'
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"TikTok API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            raise TikTokPostingError(error_msg)
        except Exception as e:
            error_msg = f"TikTok posting failed: {str(e)}"
            logger.error(error_msg)
            raise TikTokPostingError(error_msg)

    @staticmethod
    def _initialize_upload(
        open_id: str,
        access_token: str,
        video_size: int,
        caption: str
    ) -> Dict[str, Any]:
        """
        Initialize video upload and get upload URL

        Args:
            open_id: TikTok user's open_id
            access_token: Access token
            video_size: Size of video in bytes
            caption: Video caption/title

        Returns upload_url and publish_id
        """
        url = f"{TikTokPostingService.API_BASE}post/publish/video/init/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        # Use FILE_UPLOAD to avoid URL validation requirements
        payload = {
            "post_info": {
                "title": caption[:150] if caption else "Video",  # Title max 150 chars for TikTok
                "privacy_level": "PUBLIC_TO_EVERYONE",  # Production setting - posts are public (requires approved TikTok app)
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",  # Use file upload instead of PULL_FROM_URL
                "video_size": video_size,
                "chunk_size": video_size,  # Upload in single chunk
                "total_chunk_count": 1
            }
        }

        logger.info(f"TikTok API Request Payload: {payload}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def _upload_video(upload_url: str, video_data: bytes):
        """Upload video binary data to TikTok with retry logic"""
        video_size = len(video_data)
        headers = {
            "Content-Type": "video/mp4",
            "Content-Length": str(video_size),
            "Content-Range": f"bytes 0-{video_size-1}/{video_size}"
        }

        # Retry logic with exponential backoff for timeouts
        max_retries = 3
        base_timeout = 180  # Start with 3 minutes

        for attempt in range(max_retries):
            try:
                timeout = base_timeout * (attempt + 1)  # 3min, 6min, 9min
                logger.info(f"Upload attempt {attempt + 1}/{max_retries}, timeout: {timeout}s, size: {video_size} bytes")

                response = requests.put(upload_url, headers=headers, data=video_data, timeout=timeout)
                response.raise_for_status()

                logger.info(f"Video upload successful on attempt {attempt + 1}")
                return  # Success!

            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.warning(f"Upload timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Upload failed after {max_retries} attempts")
                    raise TikTokPostingError(f"Video upload timed out after {max_retries} attempts")
            except requests.exceptions.RequestException as e:
                # Don't retry on other errors (like 4xx, 5xx)
                logger.error(f"Upload failed with non-timeout error: {e}")
                raise

    @staticmethod
    def _publish_video(
        open_id: str,
        publish_id: str,
        caption: str,
        access_token: str
    ) -> Dict[str, Any]:
        """Publish the uploaded video"""
        url = f"{TikTokPostingService.API_BASE}post/publish/status/fetch/"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        payload = {
            "publish_id": publish_id
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()
