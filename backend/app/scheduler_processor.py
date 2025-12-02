"""
Scheduler Processor Lambda
Triggered by EventBridge every minute to check for and execute scheduled posts
"""
import os
import logging
from typing import Dict, Any
from scheduled_posts_manager import (
    get_posts_ready_to_publish,
    mark_post_as_processing,
    mark_post_as_posted,
    mark_post_as_failed
)
from upload_requests import create_upload_request

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    EventBridge scheduled trigger handler
    Checks for scheduled posts ready to publish and queues them

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Dict with processing results
    """
    logger.info("Scheduler processor started")

    try:
        # Get all posts ready to publish
        ready_posts = get_posts_ready_to_publish()

        logger.info(f"Found {len(ready_posts)} posts ready to publish")

        processed_count = 0
        failed_count = 0

        for post in ready_posts:
            scheduled_post_id = post['scheduled_post_id']
            user_id = post['user_id']

            try:
                logger.info(f"Processing scheduled post {scheduled_post_id} for user {user_id}")

                # Atomically mark as processing to avoid duplicate execution
                # Returns False if already being processed by another execution
                if not mark_post_as_processing(user_id, scheduled_post_id):
                    logger.info(f"Scheduled post {scheduled_post_id} already being processed, skipping")
                    continue

                # Create upload request (this will queue the posting jobs)
                upload_request = create_upload_request(
                    user_id=user_id,
                    video_url=post['video_url'],
                    caption=post['caption'],
                    destinations=post['destinations'],
                    tiktok_settings=post.get('tiktok_settings')
                )

                request_id = upload_request['request_id']

                # Mark as posted with the request_id for tracking
                mark_post_as_posted(user_id, scheduled_post_id, request_id)

                logger.info(f"Successfully queued scheduled post {scheduled_post_id} as request {request_id}")
                processed_count += 1

            except Exception as e:
                error_msg = f"Failed to process scheduled post {scheduled_post_id}: {str(e)}"
                logger.error(error_msg)

                # Mark as failed
                try:
                    mark_post_as_failed(user_id, scheduled_post_id, str(e))
                except Exception as mark_error:
                    logger.error(f"Failed to mark post as failed: {str(mark_error)}")

                failed_count += 1

        result = {
            'statusCode': 200,
            'total_ready': len(ready_posts),
            'processed': processed_count,
            'failed': failed_count
        }

        logger.info(f"Scheduler processor completed: {result}")
        return result

    except Exception as e:
        error_msg = f"Scheduler processor failed: {str(e)}"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'error': error_msg
        }
