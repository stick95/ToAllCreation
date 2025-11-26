"""
LinkedIn Posting Service
Handles posting videos to LinkedIn using their API
"""
import requests
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class LinkedInPostingError(Exception):
    """Custom exception for LinkedIn posting errors"""
    pass


class LinkedInPostingService:
    """Service for posting videos to LinkedIn"""

    API_BASE = "https://api.linkedin.com/v2"

    @staticmethod
    def post_video(
        person_urn: str,
        access_token: str,
        video_url: str,
        caption: str
    ) -> Dict[str, Any]:
        """
        Post a video to LinkedIn

        Args:
            person_urn: LinkedIn person URN (e.g., urn:li:person:ABC123)
            access_token: LinkedIn access token
            video_url: Public URL to the video file
            caption: Post caption/text

        Returns:
            Dict containing post ID and status
        """
        try:
            logger.info(f"Starting LinkedIn video post for person {person_urn}")

            # Step 1: Register video upload
            logger.info("Step 1: Registering video upload with LinkedIn")
            upload_request = LinkedInPostingService._register_video_upload(
                person_urn, access_token
            )

            logger.info(f"Upload request response: {upload_request}")

            # LinkedIn returns asset URN in the 'value' field
            video_urn = upload_request['value']['asset']
            upload_url = upload_request['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']

            logger.info(f"Video URN: {video_urn}")
            logger.info(f"Upload URL received")

            # Step 2: Download video from S3
            logger.info("Step 2: Downloading video from S3")
            video_response = requests.get(video_url, timeout=60)
            video_response.raise_for_status()
            video_data = video_response.content
            logger.info(f"Downloaded {len(video_data)} bytes")

            # Step 3: Upload video to LinkedIn
            logger.info("Step 3: Uploading video to LinkedIn")
            LinkedInPostingService._upload_video(upload_url, video_data, access_token)

            # Step 4: Wait for video processing
            logger.info("Step 4: Waiting for LinkedIn to process video")
            LinkedInPostingService._wait_for_video_processing(video_urn, access_token)

            # Step 5: Create post with video
            logger.info("Step 5: Creating LinkedIn post")
            post_result = LinkedInPostingService._create_post(
                person_urn, video_urn, caption, access_token
            )

            logger.info(f"LinkedIn post created successfully: {post_result}")

            return {
                'platform': 'linkedin',
                'post_id': post_result.get('id'),
                'video_urn': video_urn,
                'status': 'success'
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"LinkedIn API request failed: {str(e)}"
            if hasattr(e.response, 'text'):
                error_msg += f" - Response: {e.response.text}"
            logger.error(error_msg)
            raise LinkedInPostingError(error_msg)
        except Exception as e:
            error_msg = f"LinkedIn posting failed: {str(e)}"
            logger.error(error_msg)
            raise LinkedInPostingError(error_msg)

    @staticmethod
    def _register_video_upload(person_urn: str, access_token: str) -> Dict[str, Any]:
        """Register a video upload with LinkedIn"""
        url = f"{LinkedInPostingService.API_BASE}/assets?action=registerUpload"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        payload = {
            "registerUploadRequest": {
                "recipes": [
                    "urn:li:digitalmediaRecipe:feedshare-video"
                ],
                "owner": person_urn,
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent"
                    }
                ]
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def _upload_video(upload_url: str, video_data: bytes, access_token: str):
        """Upload video binary data to LinkedIn"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/octet-stream'
        }

        response = requests.put(upload_url, headers=headers, data=video_data, timeout=300)
        response.raise_for_status()

    @staticmethod
    def _wait_for_video_processing(video_urn: str, access_token: str, max_wait_seconds: int = 120):
        """Wait for LinkedIn to finish processing the video"""
        # Extract asset ID from URN (e.g., urn:li:digitalmediaAsset:C5622xxx -> C5622xxx)
        asset_id = video_urn.split(':')[-1]
        url = f"{LinkedInPostingService.API_BASE}/assets/{asset_id}"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            asset = response.json()
            status = asset.get('status')

            logger.info(f"Video processing status: {status}")

            # LinkedIn video statuses: ALLOWED means video can be used in posts
            if status in ['AVAILABLE', 'ALLOWED']:
                return
            elif status in ['FAILED', 'PROCESSING_FAILED']:
                raise LinkedInPostingError(f"Video processing failed with status: {status}")

            time.sleep(5)

        raise LinkedInPostingError("Video processing timeout - LinkedIn took too long to process the video")

    @staticmethod
    def _create_post(person_urn: str, video_urn: str, caption: str, access_token: str) -> Dict[str, Any]:
        """Create a LinkedIn post with the video"""
        url = f"{LinkedInPostingService.API_BASE}/ugcPosts"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
            'X-Restli-Protocol-Version': '2.0.0'
        }

        payload = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": caption
                    },
                    "shareMediaCategory": "VIDEO",
                    "media": [
                        {
                            "status": "READY",
                            "media": video_urn
                        }
                    ]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        return response.json()
