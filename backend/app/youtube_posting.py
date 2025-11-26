"""
YouTube Shorts Posting Service
Handles uploading videos to YouTube using YouTube Data API v3
Videos under 60 seconds with vertical aspect ratio automatically become Shorts
"""
import requests
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class YouTubePostingError(Exception):
    """Custom exception for YouTube posting errors"""
    pass


class YouTubePostingService:
    """Service for posting videos to YouTube (as Shorts)"""

    API_BASE = "https://www.googleapis.com/youtube/v3"
    UPLOAD_API_BASE = "https://www.googleapis.com/upload/youtube/v3"

    @staticmethod
    def post_video(
        access_token: str,
        video_url: str,
        title: str,
        description: Optional[str] = None,
        privacy_status: str = "public",
        tags: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Upload video to YouTube (becomes a Short if ≤60s and vertical)

        Process:
        1. Download video from S3
        2. Upload video to YouTube with resumable upload
        3. Set video metadata (title, description, privacy)

        Args:
            access_token: OAuth 2.0 access token
            video_url: Publicly accessible URL to the video file
            title: Video title (max 100 chars for Shorts)
            description: Video description (optional)
            privacy_status: Video privacy (public, private, unlisted)
            tags: Video tags (optional)

        Returns:
            Dict with video information including video_id

        Raises:
            YouTubePostingError: If posting fails
        """
        try:
            # Step 1: Download video
            logger.info(f"Downloading video from {video_url}")
            video_response = requests.get(video_url, stream=True, timeout=60)

            if video_response.status_code != 200:
                raise YouTubePostingError(f"Failed to download video: HTTP {video_response.status_code}")

            video_data = video_response.content
            video_size = len(video_data)

            logger.info(f"Downloaded video: {video_size} bytes")

            # Step 2: Prepare metadata
            # Add #Shorts to description to help YouTube identify it as a Short
            full_description = description or ""
            if "#Shorts" not in full_description and "#shorts" not in full_description:
                full_description = f"{full_description}\n\n#Shorts".strip()

            metadata = {
                "snippet": {
                    "title": title[:100],  # YouTube Shorts title limit
                    "description": full_description,
                    "tags": tags or ["Shorts"],
                    "categoryId": "22"  # People & Blogs category
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False
                }
            }

            # Step 3: Upload video using resumable upload
            video_id = YouTubePostingService._resumable_upload(
                access_token=access_token,
                video_data=video_data,
                metadata=metadata
            )

            logger.info(f"Video uploaded successfully: video_id={video_id}")

            return {
                "success": True,
                "video_id": video_id,
                "platform": "youtube",
                "title": title,
                "url": f"https://www.youtube.com/shorts/{video_id}"
            }

        except YouTubePostingError:
            raise
        except Exception as e:
            logger.error(f"YouTube posting error: {e}")
            raise YouTubePostingError(f"Failed to post video: {str(e)}")

    @staticmethod
    def _resumable_upload(
        access_token: str,
        video_data: bytes,
        metadata: Dict
    ) -> str:
        """
        Upload video using YouTube's resumable upload protocol

        Process:
        1. Initialize upload session
        2. Upload video bytes
        3. Get video ID from response

        Args:
            access_token: OAuth 2.0 access token
            video_data: Video file bytes
            metadata: Video metadata

        Returns:
            video_id string
        """
        # Step 1: Initialize upload
        init_url = f"{YouTubePostingService.UPLOAD_API_BASE}/videos?uploadType=resumable&part=snippet,status"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Upload-Content-Length": str(len(video_data)),
            "X-Upload-Content-Type": "video/*"
        }

        logger.info(f"Initializing resumable upload: {len(video_data)} bytes")
        init_response = requests.post(init_url, headers=headers, json=metadata, timeout=30)

        if init_response.status_code not in [200, 201]:
            error_data = init_response.json() if init_response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            logger.error(f"Upload initialization failed: {error_msg}")
            raise YouTubePostingError(f"Upload initialization failed: {error_msg}")

        # Get upload URL from Location header
        upload_url = init_response.headers.get("Location")
        if not upload_url:
            raise YouTubePostingError("No upload URL received from YouTube")

        logger.info(f"Upload session initialized: {upload_url}")

        # Step 2: Upload video data
        upload_headers = {
            "Content-Type": "video/*",
            "Content-Length": str(len(video_data))
        }

        logger.info(f"Uploading video data: {len(video_data)} bytes")
        upload_response = requests.put(
            upload_url,
            headers=upload_headers,
            data=video_data,
            timeout=300  # 5 minutes for upload
        )

        if upload_response.status_code not in [200, 201]:
            error_data = upload_response.json() if upload_response.text else {}
            error_msg = error_data.get("error", {}).get("message", "Unknown error")
            logger.error(f"Video upload failed: {error_msg}")
            raise YouTubePostingError(f"Video upload failed: {error_msg}")

        # Step 3: Extract video ID
        response_data = upload_response.json()
        video_id = response_data.get("id")

        if not video_id:
            raise YouTubePostingError("No video ID received from YouTube")

        logger.info(f"Video uploaded: video_id={video_id}")
        return video_id

    @staticmethod
    def get_channel_info(access_token: str) -> Dict:
        """
        Get authenticated user's YouTube channel information

        Args:
            access_token: OAuth 2.0 access token

        Returns:
            Channel information including channel_id and title
        """
        url = f"{YouTubePostingService.API_BASE}/channels?part=snippet&mine=true"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "items" not in data or len(data["items"]) == 0:
                raise YouTubePostingError("No YouTube channel found for this account")

            channel = data["items"][0]
            return {
                "channel_id": channel["id"],
                "title": channel["snippet"]["title"],
                "description": channel["snippet"].get("description", ""),
                "thumbnail": channel["snippet"]["thumbnails"]["default"]["url"]
            }

        except requests.RequestException as e:
            logger.error(f"Failed to get channel info: {e}")
            raise YouTubePostingError(f"Failed to get channel info: {str(e)}")
