"""
Twitter (X) Posting Service
Handles posting tweets with videos using Twitter API v1.1 (media) + v2 (tweets)
"""
import requests
import logging
import os
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TwitterPostingError(Exception):
    """Custom exception for Twitter posting errors"""
    pass

class TwitterPostingService:
    """Service for posting content to Twitter (X)"""

    # Twitter API v1.1 for media upload
    UPLOAD_API_BASE = "https://upload.twitter.com/1.1"
    # Twitter API v2 for tweet creation
    API_V2_BASE = "https://api.twitter.com/2"

    # Video upload limits
    MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512 MB
    CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB chunks

    @staticmethod
    def post_video(
        access_token: str,
        video_url: str,
        text: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet with video

        Process:
        1. Download video from S3
        2. Upload video to Twitter using chunked upload (v1.1 API)
        3. Create tweet with media_id (v2 API)

        Args:
            access_token: OAuth 2.0 access token
            video_url: Publicly accessible URL to the video file
            text: Tweet text (optional, max 280 chars)
            user_id: Twitter user ID (optional, for validation)

        Returns:
            Dict with tweet information including tweet_id

        Raises:
            TwitterPostingError: If posting fails
        """
        try:
            # Step 1: Download video
            logger.info(f"Downloading video from {video_url}")
            video_response = requests.get(video_url, stream=True, timeout=60)

            if video_response.status_code != 200:
                raise TwitterPostingError(f"Failed to download video: HTTP {video_response.status_code}")

            video_data = video_response.content
            video_size = len(video_data)

            logger.info(f"Downloaded video: {video_size} bytes")

            if video_size > TwitterPostingService.MAX_VIDEO_SIZE:
                raise TwitterPostingError(f"Video too large: {video_size} bytes (max {TwitterPostingService.MAX_VIDEO_SIZE})")

            # Step 2: Upload video using chunked upload
            media_id = TwitterPostingService._chunked_upload(
                access_token=access_token,
                video_data=video_data,
                media_type="video/mp4"
            )

            logger.info(f"Video uploaded successfully: media_id={media_id}")

            # Step 3: Create tweet with media
            tweet_data = TwitterPostingService._create_tweet(
                access_token=access_token,
                text=text or "",
                media_ids=[media_id]
            )

            logger.info(f"Tweet posted successfully: tweet_id={tweet_data['id']}")

            return {
                "success": True,
                "tweet_id": tweet_data["id"],
                "media_id": media_id,
                "platform": "twitter",
                "text": tweet_data.get("text", text)
            }

        except TwitterPostingError:
            raise
        except Exception as e:
            logger.error(f"Twitter posting error: {e}")
            raise TwitterPostingError(f"Failed to post tweet: {str(e)}")

    @staticmethod
    def _chunked_upload(
        access_token: str,
        video_data: bytes,
        media_type: str = "video/mp4"
    ) -> str:
        """
        Upload video using chunked upload (v1.1 API)

        Process:
        1. INIT: Initialize upload
        2. APPEND: Upload chunks
        3. FINALIZE: Complete upload

        Args:
            access_token: OAuth 2.0 access token
            video_data: Video file bytes
            media_type: MIME type

        Returns:
            media_id string
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # Step 1: INIT
        init_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        init_params = {
            "command": "INIT",
            "total_bytes": len(video_data),
            "media_type": media_type,
            "media_category": "tweet_video"  # Required for videos
        }

        logger.info(f"Initializing upload: {len(video_data)} bytes")
        init_response = requests.post(init_url, headers=headers, data=init_params, timeout=30)

        if init_response.status_code != 200 and init_response.status_code != 201:
            error_data = init_response.json() if init_response.text else {}
            error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown error")
            logger.error(f"Upload INIT failed: {error_msg}")
            raise TwitterPostingError(f"Upload initialization failed: {error_msg}")

        init_data = init_response.json()
        media_id = init_data["media_id_string"]

        logger.info(f"Upload initialized: media_id={media_id}")

        # Step 2: APPEND chunks
        append_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        offset = 0
        segment_index = 0

        while offset < len(video_data):
            chunk = video_data[offset:offset + TwitterPostingService.CHUNK_SIZE]

            append_params = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_index
            }

            files = {
                "media": chunk
            }

            logger.info(f"Uploading chunk {segment_index}: offset={offset}, size={len(chunk)}")
            append_response = requests.post(
                append_url,
                headers=headers,
                data=append_params,
                files=files,
                timeout=60
            )

            if append_response.status_code not in [200, 201, 204]:
                error_data = append_response.json() if append_response.text else {}
                error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown error")
                logger.error(f"Upload APPEND failed: {error_msg}")
                raise TwitterPostingError(f"Chunk upload failed: {error_msg}")

            offset += len(chunk)
            segment_index += 1

        logger.info(f"All chunks uploaded: {segment_index} segments")

        # Step 3: FINALIZE
        finalize_params = {
            "command": "FINALIZE",
            "media_id": media_id
        }

        logger.info("Finalizing upload...")
        finalize_response = requests.post(
            append_url,
            headers=headers,
            data=finalize_params,
            timeout=30
        )

        if finalize_response.status_code not in [200, 201]:
            error_data = finalize_response.json() if finalize_response.text else {}
            error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown error")
            logger.error(f"Upload FINALIZE failed: {error_msg}")
            raise TwitterPostingError(f"Upload finalization failed: {error_msg}")

        finalize_data = finalize_response.json()

        # Check if video processing is required
        processing_info = finalize_data.get("processing_info")
        if processing_info:
            state = processing_info.get("state")
            logger.info(f"Video processing: state={state}")

            # Wait for processing if needed
            if state in ["pending", "in_progress"]:
                TwitterPostingService._wait_for_processing(
                    access_token=access_token,
                    media_id=media_id
                )

        logger.info(f"Upload finalized: media_id={media_id}")
        return media_id

    @staticmethod
    def _wait_for_processing(
        access_token: str,
        media_id: str,
        max_wait: int = 300,
        check_interval: int = 5
    ):
        """
        Wait for video processing to complete

        Args:
            access_token: OAuth 2.0 access token
            media_id: Media ID to check
            max_wait: Maximum wait time in seconds
            check_interval: How often to check (seconds)
        """
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        status_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        status_params = {
            "command": "STATUS",
            "media_id": media_id
        }

        elapsed = 0
        while elapsed < max_wait:
            logger.info(f"Checking processing status: elapsed={elapsed}s")

            response = requests.get(status_url, headers=headers, params=status_params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                processing_info = data.get("processing_info", {})
                state = processing_info.get("state")

                if state == "succeeded":
                    logger.info("Video processing succeeded")
                    return
                elif state == "failed":
                    error = processing_info.get("error", {})
                    error_msg = error.get("message", "Processing failed")
                    raise TwitterPostingError(f"Video processing failed: {error_msg}")

                # Still processing
                check_after = processing_info.get("check_after_secs", check_interval)
                time.sleep(check_after)
                elapsed += check_after
            else:
                # Status check failed, wait and retry
                time.sleep(check_interval)
                elapsed += check_interval

        raise TwitterPostingError(f"Video processing timeout after {max_wait}s")

    @staticmethod
    def _create_tweet(
        access_token: str,
        text: str,
        media_ids: list
    ) -> Dict:
        """
        Create tweet with media (v2 API)

        Args:
            access_token: OAuth 2.0 access token
            text: Tweet text (max 280 chars)
            media_ids: List of media IDs

        Returns:
            Tweet data including tweet ID
        """
        url = f"{TwitterPostingService.API_V2_BASE}/tweets"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Truncate text if too long
        if len(text) > 280:
            text = text[:277] + "..."

        payload = {
            "text": text
        }

        if media_ids:
            payload["media"] = {
                "media_ids": [str(mid) for mid in media_ids]
            }

        logger.info(f"Creating tweet: text_length={len(text)}, media_count={len(media_ids)}")

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code not in [200, 201]:
            error_data = response.json() if response.text else {}

            # Twitter v2 error format
            if "errors" in error_data:
                error_msg = error_data["errors"][0].get("message", "Unknown error")
            else:
                error_msg = error_data.get("detail", "Unknown error")

            logger.error(f"Tweet creation failed: {error_msg}")
            raise TwitterPostingError(f"Failed to create tweet: {error_msg}")

        tweet_data = response.json()
        return tweet_data.get("data", tweet_data)
