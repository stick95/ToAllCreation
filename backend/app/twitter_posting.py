"""
Twitter (X) Posting Service
Handles posting tweets with videos using Twitter API v1.1 (media) + v2 (tweets)
Uses OAuth 1.0a for media upload and OAuth 2.0 for tweet creation
"""
import requests
import logging
import os
import time
import hmac
import hashlib
import base64
import secrets
from urllib.parse import quote, urlencode
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
    def _generate_oauth1a_header(
        method: str,
        url: str,
        params: Dict[str, str],
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str
    ) -> str:
        """
        Generate OAuth 1.0a authorization header

        Args:
            method: HTTP method (POST, GET)
            url: Full URL
            params: Request parameters
            api_key: Twitter API Key (consumer key)
            api_secret: Twitter API Secret (consumer secret)
            access_token: User access token
            access_token_secret: User access token secret

        Returns:
            OAuth authorization header value
        """
        # OAuth parameters
        oauth_nonce = secrets.token_hex(16)
        oauth_timestamp = str(int(time.time()))

        oauth_params = {
            'oauth_consumer_key': api_key,
            'oauth_nonce': oauth_nonce,
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_timestamp': oauth_timestamp,
            'oauth_token': access_token,
            'oauth_version': '1.0'
        }

        # Combine all parameters
        all_params = {**params, **oauth_params}

        # Create signature base string
        sorted_params = sorted(all_params.items())
        param_string = '&'.join([f'{quote(str(k), safe="")}={quote(str(v), safe="")}' for k, v in sorted_params])

        signature_base = f'{method.upper()}&{quote(url, safe="")}&{quote(param_string, safe="")}'

        # Create signing key
        signing_key = f'{quote(api_secret, safe="")}&{quote(access_token_secret, safe="")}'

        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode(),
                signature_base.encode(),
                hashlib.sha1
            ).digest()
        ).decode()

        oauth_params['oauth_signature'] = signature

        # Build authorization header
        auth_header = 'OAuth ' + ', '.join([f'{quote(k, safe="")}="{quote(v, safe="")}"' for k, v in sorted(oauth_params.items())])

        return auth_header

    @staticmethod
    def post_video(
        access_token: str,
        video_url: str,
        text: Optional[str] = None,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a tweet with video

        Process:
        1. Download video from S3
        2. Upload video to Twitter using chunked upload (v1.1 API with OAuth 1.0a)
        3. Create tweet with media_id (v2 API with OAuth 2.0)

        Args:
            access_token: OAuth 2.0 access token (for tweet creation)
            video_url: Publicly accessible URL to the video file
            text: Tweet text (optional, max 280 chars)
            user_id: Twitter user ID (optional, for validation)
            api_key: Twitter API Key for OAuth 1.0a (media upload)
            api_secret: Twitter API Secret for OAuth 1.0a (media upload)
            access_token_secret: OAuth 1.0a access token secret (media upload)

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

            # Step 2: Upload video using chunked upload (OAuth 1.0a)
            media_id = TwitterPostingService._chunked_upload(
                video_data=video_data,
                media_type="video/mp4",
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            logger.info(f"Video uploaded successfully: media_id={media_id}")

            # Step 3: Create tweet with media (using OAuth 1.0a)
            tweet_data = TwitterPostingService._create_tweet(
                access_token=access_token,
                text=text or "",
                media_ids=[media_id],
                api_key=api_key,
                api_secret=api_secret,
                access_token_secret=access_token_secret
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
        video_data: bytes,
        media_type: str = "video/mp4",
        api_key: str = None,
        api_secret: str = None,
        access_token: str = None,
        access_token_secret: str = None
    ) -> str:
        """
        Upload video using chunked upload (v1.1 API with OAuth 1.0a)

        Process:
        1. INIT: Initialize upload
        2. APPEND: Upload chunks
        3. FINALIZE: Complete upload

        Args:
            video_data: Video file bytes
            media_type: MIME type
            api_key: Twitter API Key (OAuth 1.0a consumer key)
            api_secret: Twitter API Secret (OAuth 1.0a consumer secret)
            access_token: OAuth 1.0a access token
            access_token_secret: OAuth 1.0a access token secret

        Returns:
            media_id string
        """
        # Step 1: INIT
        init_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        init_params = {
            "command": "INIT",
            "total_bytes": str(len(video_data)),
            "media_type": media_type,
            "media_category": "tweet_video"  # Required for videos
        }

        # Generate OAuth 1.0a header for INIT
        auth_header = TwitterPostingService._generate_oauth1a_header(
            method="POST",
            url=init_url,
            params=init_params,
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        headers = {
            "Authorization": auth_header
        }

        logger.info(f"Initializing upload: {len(video_data)} bytes")
        init_response = requests.post(init_url, headers=headers, data=init_params, timeout=30)

        if init_response.status_code not in [200, 201, 202]:
            logger.error(f"Upload INIT failed with status {init_response.status_code}")
            logger.error(f"Response text: {init_response.text}")
            error_data = init_response.json() if init_response.text else {}
            logger.error(f"Error data: {error_data}")
            error_msg = error_data.get("errors", [{}])[0].get("message", "Unknown error")
            logger.error(f"Upload INIT failed: {error_msg}")
            raise TwitterPostingError(f"Upload initialization failed: {error_msg} (Status: {init_response.status_code})")

        init_data = init_response.json()
        media_id = init_data["media_id_string"]

        logger.info(f"Upload initialized: media_id={media_id}")

        # Step 2: APPEND chunks
        append_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        offset = 0
        segment_index = 0

        while offset < len(video_data):
            chunk = video_data[offset:offset + TwitterPostingService.CHUNK_SIZE]

            # For multipart uploads, parameters must be in query string for OAuth signature
            append_params = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": str(segment_index)
            }

            # Build URL with query parameters
            from urllib.parse import urlencode
            append_url_with_params = f"{append_url}?{urlencode(append_params)}"

            # Generate OAuth 1.0a header for APPEND
            # Include query params in signature
            append_auth_header = TwitterPostingService._generate_oauth1a_header(
                method="POST",
                url=append_url,
                params=append_params,
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            append_headers = {
                "Authorization": append_auth_header
            }

            files = {
                "media": chunk
            }

            logger.info(f"Uploading chunk {segment_index}: offset={offset}, size={len(chunk)}")
            append_response = requests.post(
                append_url_with_params,
                headers=append_headers,
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
        finalize_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        finalize_params = {
            "command": "FINALIZE",
            "media_id": media_id
        }

        # Generate OAuth 1.0a header for FINALIZE
        finalize_auth_header = TwitterPostingService._generate_oauth1a_header(
            method="POST",
            url=finalize_url,
            params=finalize_params,
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        finalize_headers = {
            "Authorization": finalize_auth_header
        }

        logger.info("Finalizing upload...")
        finalize_response = requests.post(
            finalize_url,
            headers=finalize_headers,
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
                    media_id=media_id,
                    api_key=api_key,
                    api_secret=api_secret,
                    access_token=access_token,
                    access_token_secret=access_token_secret
                )

        logger.info(f"Upload finalized: media_id={media_id}")
        return media_id

    @staticmethod
    def _wait_for_processing(
        media_id: str,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
        max_wait: int = 300,
        check_interval: int = 5
    ):
        """
        Wait for video processing to complete

        Args:
            media_id: Media ID to check
            api_key: Twitter API Key (OAuth 1.0a consumer key)
            api_secret: Twitter API Secret (OAuth 1.0a consumer secret)
            access_token: OAuth 1.0a access token
            access_token_secret: OAuth 1.0a access token secret
            max_wait: Maximum wait time in seconds
            check_interval: How often to check (seconds)
        """
        status_url = f"{TwitterPostingService.UPLOAD_API_BASE}/media/upload.json"
        status_params = {
            "command": "STATUS",
            "media_id": media_id
        }

        elapsed = 0
        while elapsed < max_wait:
            logger.info(f"Checking processing status: elapsed={elapsed}s")

            # Generate OAuth 1.0a header for STATUS
            status_auth_header = TwitterPostingService._generate_oauth1a_header(
                method="GET",
                url=status_url,
                params=status_params,
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            headers = {
                "Authorization": status_auth_header
            }

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
        media_ids: list,
        api_key: str = None,
        api_secret: str = None,
        access_token_secret: str = None
    ) -> Dict:
        """
        Create tweet with media (v2 API with OAuth 1.0a)

        Args:
            access_token: OAuth 1.0a access token
            text: Tweet text (max 280 chars)
            media_ids: List of media IDs
            api_key: Twitter API Key (OAuth 1.0a consumer key)
            api_secret: Twitter API Secret (OAuth 1.0a consumer secret)
            access_token_secret: OAuth 1.0a access token secret

        Returns:
            Tweet data including tweet ID
        """
        url = f"{TwitterPostingService.API_V2_BASE}/tweets"

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

        # Generate OAuth 1.0a header for tweet creation
        # For POST with JSON body, we don't include body params in signature
        auth_header = TwitterPostingService._generate_oauth1a_header(
            method="POST",
            url=url,
            params={},  # No query params for this endpoint
            api_key=api_key,
            api_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )

        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
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
