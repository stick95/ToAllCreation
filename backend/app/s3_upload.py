"""
S3 Upload Helper
Generates presigned URLs for direct S3 uploads from browser
"""
import boto3
from botocore.client import Config
import uuid
from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

class S3UploadHelper:
    """Helper for generating presigned S3 upload URLs"""

    @staticmethod
    def generate_presigned_upload_url(
        user_id: str,
        filename: str,
        content_type: str = "video/mp4"
    ) -> Dict[str, str]:
        """
        Generate a presigned URL for uploading a video directly to S3

        Args:
            user_id: User ID (for organizing uploads)
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            Dict with 'upload_url' and 's3_key'
        """
        try:
            bucket_name = os.environ.get('VIDEO_UPLOAD_BUCKET', 'toallcreation-video-uploads')

            # Create S3 client with explicit regional endpoint to avoid 307 redirects
            # Must use endpoint_url to force regional URLs in presigned URLs
            s3_client = boto3.client(
                's3',
                region_name='us-west-2',
                endpoint_url='https://s3.us-west-2.amazonaws.com',
                config=Config(signature_version='s3v4')
            )

            # Generate unique S3 key
            file_extension = filename.split('.')[-1] if '.' in filename else 'mp4'
            s3_key = f"uploads/{user_id}/{uuid.uuid4()}.{file_extension}"

            # Generate presigned URL (valid for 10 minutes)
            # Don't include ContentType in params - it will be sent as header
            presigned_url = s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=600  # 10 minutes
            )

            logger.info(f"Generated presigned URL for {s3_key}")

            return {
                'upload_url': presigned_url,
                's3_key': s3_key,
                'bucket': bucket_name
            }

        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    @staticmethod
    def get_public_url(bucket: str, s3_key: str) -> str:
        """Get public URL for an S3 object"""
        return f"https://{bucket}.s3.amazonaws.com/{s3_key}"
