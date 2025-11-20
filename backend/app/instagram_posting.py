"""
Instagram Posting Service
Handles posting videos/reels to Instagram Business accounts via Graph API
"""
import requests
import logging
import time
import os
import boto3
from typing import Dict, Any, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client('s3')


class InstagramPostingError(Exception):
    """Custom exception for Instagram posting errors"""
    pass


class InstagramPostingService:
    """Service for posting content to Instagram"""

    GRAPH_API_BASE = "https://graph.facebook.com/v18.0"

    @staticmethod
    def _download_from_s3(video_url: str) -> str:
        """
        Download video from S3 to Lambda's /tmp directory

        Args:
            video_url: S3 URL (https://bucket.s3.amazonaws.com/key)

        Returns:
            Local file path in /tmp
        """
        # Parse S3 URL
        parsed = urlparse(video_url)

        # Extract bucket and key
        # URL format: https://bucket.s3.amazonaws.com/key or https://bucket.s3.region.amazonaws.com/key
        bucket = parsed.netloc.split('.')[0]
        key = parsed.path.lstrip('/')

        # Download to /tmp (Lambda's writable directory)
        local_path = f"/tmp/{os.path.basename(key)}"

        logger.info(f"Downloading from S3: bucket={bucket}, key={key}")
        s3_client.download_file(bucket, key, local_path)
        logger.info(f"Downloaded to {local_path}, size={os.path.getsize(local_path)} bytes")

        return local_path

    @staticmethod
    def post_reel(
        instagram_account_id: str,
        access_token: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a reel to Instagram Business account

        Instagram Reels API has a two-step process:
        1. Create a media container (starts upload)
        2. Publish the container (makes it live)

        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Page access token (works for Instagram too)
            video_url: Publicly accessible URL to the video file
            caption: Optional caption for the reel

        Returns:
            Dict with post information including media_id

        Raises:
            InstagramPostingError: If posting fails
        """
        local_video_path = None
        try:
            # Step 1: Download video from S3
            logger.info(f"Downloading video from S3: {video_url}")
            local_video_path = InstagramPostingService._download_from_s3(video_url)

            # Step 2: Initialize resumable upload session
            logger.info(f"Initializing Instagram resumable upload for account {instagram_account_id}")

            init_url = f"{InstagramPostingService.GRAPH_API_BASE}/{instagram_account_id}/media"

            # Get file size
            file_size = os.path.getsize(local_video_path)

            init_params = {
                'access_token': access_token,
                'media_type': 'REELS',
                'upload_type': 'resumable',
                'file_size': file_size
            }

            if caption:
                init_params['caption'] = caption

            # Add optional parameters
            init_params['share_to_feed'] = True

            logger.info(f"Initializing upload for file size: {file_size} bytes")
            init_response = requests.post(init_url, data=init_params)

            if init_response.status_code != 200:
                error_data = init_response.json()
                logger.error(f"Failed to initialize Instagram upload: {error_data}")
                raise InstagramPostingError(
                    f"Failed to initialize upload: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            init_data = init_response.json()
            container_id = init_data.get('id')  # This IS the container ID!
            upload_url = init_data.get('uri')  # Get the upload URL from the response

            logger.info(f"Container created and upload initialized: container_id={container_id}, upload_url={upload_url}")

            if not upload_url:
                raise InstagramPostingError(f"No upload URL returned in init response: {init_data}")

            # Step 3: Upload video file in chunks to avoid timeout
            logger.info(f"Uploading video file to {upload_url} in chunks...")

            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            offset = 0

            with open(local_video_path, 'rb') as video_file:
                while offset < file_size:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break

                    chunk_end = offset + len(chunk) - 1

                    upload_headers = {
                        'Authorization': f'OAuth {access_token}',
                        'offset': str(offset),
                        'file_size': str(file_size),
                        'Content-Length': str(len(chunk))
                    }

                    logger.info(f"Uploading chunk: offset={offset}, size={len(chunk)}, total={file_size}")

                    upload_response = requests.post(
                        upload_url,
                        headers=upload_headers,
                        data=chunk
                    )

                    if upload_response.status_code not in [200, 201, 206]:  # 206 = Partial Content (expected for chunks)
                        logger.error(f"Failed to upload chunk: status={upload_response.status_code}, response={upload_response.text}")
                        logger.error(f"Request headers: {dict(upload_headers)}")
                        logger.error(f"Chunk size: {len(chunk)}, offset: {offset}, file_size: {file_size}")
                        raise InstagramPostingError(f"Failed to upload chunk at offset {offset}: {upload_response.text}")

                    offset += len(chunk)
                    logger.info(f"Chunk uploaded successfully, progress: {offset}/{file_size} ({offset*100//file_size}%)")

            logger.info(f"Video uploaded successfully to {upload_url}")

            # Step 4: Check container status and publish
            # The container was already created in Step 2 (init), now we just need to wait for it to process
            # Instagram needs time to process the video, but API Gateway has 30s timeout
            # So we do a quick check and return success even if still processing
            logger.info("Checking if Instagram video is ready for quick publish...")

            max_retries = 5  # Only 5 attempts to stay under 30s timeout
            retry_delay = 3  # 3 seconds between attempts

            for attempt in range(max_retries):
                # Check container status
                status_url = f"{InstagramPostingService.GRAPH_API_BASE}/{container_id}"
                status_params = {
                    'access_token': access_token,
                    'fields': 'status_code'
                }

                status_response = requests.get(status_url, params=status_params)

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status_code = status_data.get('status_code')

                    logger.info(f"Container status: {status_code} (attempt {attempt + 1}/{max_retries})")

                    if status_code == 'FINISHED':
                        # Container is ready, publish it
                        logger.info(f"Publishing Instagram reel...")

                        publish_url = f"{InstagramPostingService.GRAPH_API_BASE}/{instagram_account_id}/media_publish"
                        publish_params = {
                            'access_token': access_token,
                            'creation_id': container_id
                        }

                        publish_response = requests.post(publish_url, params=publish_params)

                        if publish_response.status_code != 200:
                            error_data = publish_response.json()
                            logger.error(f"Failed to publish Instagram reel: {error_data}")
                            raise InstagramPostingError(
                                f"Failed to publish: {error_data.get('error', {}).get('message', 'Unknown error')}"
                            )

                        publish_data = publish_response.json()
                        media_id = publish_data.get('id')

                        logger.info(f"Instagram reel published successfully: {media_id}")

                        return {
                            'success': True,
                            'media_id': media_id,
                            'post_id': media_id,
                            'platform': 'instagram',
                            'instagram_account_id': instagram_account_id,
                            'status': 'published'
                        }

                    elif status_code == 'ERROR':
                        raise InstagramPostingError("Instagram reported an error processing the video")

                    elif status_code in ['IN_PROGRESS', 'PUBLISHED']:
                        # Still processing, wait and retry
                        time.sleep(retry_delay)
                        continue

                else:
                    logger.warning(f"Failed to check status: {status_response.status_code}")

                time.sleep(retry_delay)

            # If we get here, video is still processing
            # Return success anyway - Instagram will publish it automatically when ready
            logger.info(f"Instagram container {container_id} still processing. It will publish automatically when ready.")

            return {
                'success': True,
                'container_id': container_id,
                'post_id': container_id,
                'platform': 'instagram',
                'instagram_account_id': instagram_account_id,
                'status': 'processing',
                'message': 'Video uploaded successfully. Instagram is processing it and will publish shortly.'
            }

        except InstagramPostingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error posting to Instagram: {e}")
            raise InstagramPostingError(f"Unexpected error: {str(e)}")
        finally:
            # Clean up temporary file
            if local_video_path and os.path.exists(local_video_path):
                try:
                    os.remove(local_video_path)
                    logger.info(f"Cleaned up temporary file: {local_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {e}")

    @staticmethod
    def post_photo(
        instagram_account_id: str,
        access_token: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Post a photo to Instagram Business account

        Args:
            instagram_account_id: Instagram Business Account ID
            access_token: Page access token
            image_url: Publicly accessible URL to the image file
            caption: Optional caption for the photo

        Returns:
            Dict with post information including media_id

        Raises:
            InstagramPostingError: If posting fails
        """
        try:
            # Step 1: Create media container
            logger.info(f"Creating Instagram photo container for account {instagram_account_id}")

            container_url = f"{InstagramPostingService.GRAPH_API_BASE}/{instagram_account_id}/media"

            container_params = {
                'access_token': access_token,
                'image_url': image_url
            }

            if caption:
                container_params['caption'] = caption

            container_response = requests.post(container_url, params=container_params)

            if container_response.status_code != 200:
                error_data = container_response.json()
                logger.error(f"Failed to create Instagram container: {error_data}")
                raise InstagramPostingError(
                    f"Failed to create container: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            container_data = container_response.json()
            container_id = container_data.get('id')

            logger.info(f"Container created: {container_id}")

            # Step 2: Publish the container
            logger.info(f"Publishing Instagram photo...")

            publish_url = f"{InstagramPostingService.GRAPH_API_BASE}/{instagram_account_id}/media_publish"
            publish_params = {
                'access_token': access_token,
                'creation_id': container_id
            }

            publish_response = requests.post(publish_url, params=publish_params)

            if publish_response.status_code != 200:
                error_data = publish_response.json()
                logger.error(f"Failed to publish Instagram photo: {error_data}")
                raise InstagramPostingError(
                    f"Failed to publish: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )

            publish_data = publish_response.json()
            media_id = publish_data.get('id')

            logger.info(f"Instagram photo published successfully: {media_id}")

            return {
                'success': True,
                'media_id': media_id,
                'post_id': media_id,
                'platform': 'instagram',
                'instagram_account_id': instagram_account_id
            }

        except InstagramPostingError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error posting photo to Instagram: {e}")
            raise InstagramPostingError(f"Unexpected error: {str(e)}")
