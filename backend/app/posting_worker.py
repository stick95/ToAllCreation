"""
Async Worker for Social Media Posting
Processes SQS messages to post content to social media platforms
"""
import json
import logging
import os
import traceback
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Import posting services
from instagram_posting import InstagramPostingService, InstagramPostingError
from facebook_posting import FacebookPostingService

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
upload_requests_table = dynamodb.Table(os.environ['UPLOAD_REQUESTS_TABLE'])
social_accounts_table = dynamodb.Table(os.environ['SOCIAL_ACCOUNTS_TABLE'])


class DetailedLogger:
    """Captures detailed logs for error reporting"""

    def __init__(self, request_id: str, destination: str):
        self.request_id = request_id
        self.destination = destination
        self.logs = []
        self.start_time = datetime.utcnow()

    def log(self, level: str, message: str, **kwargs):
        """Add a log entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }
        self.logs.append(entry)

        # Also log to CloudWatch
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.destination}] {message}", extra=kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """Get log summary"""
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        return {
            'total_logs': len(self.logs),
            'duration_seconds': duration,
            'error_count': len([l for l in self.logs if l['level'] == 'ERROR']),
            'warning_count': len([l for l in self.logs if l['level'] == 'WARNING'])
        }


def update_request_status(
    request_id: str,
    destination: str,
    status: str,
    logs: List[Dict],
    error: str = None,
    result: Dict = None
):
    """Update the request status in DynamoDB"""
    try:
        # Prepare the update
        update_expr = 'SET destinations.#dest.#status = :status, destinations.#dest.updated_at = :updated_at, destinations.#dest.logs = :logs'
        expr_attr_names = {
            '#dest': destination,
            '#status': 'status'
        }
        expr_attr_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat(),
            ':logs': logs
        }

        if error:
            update_expr += ', destinations.#dest.#error = :error'
            expr_attr_names['#error'] = 'error'
            expr_attr_values[':error'] = error

        if result:
            update_expr += ', destinations.#dest.#result = :result'
            expr_attr_names['#result'] = 'result'  # 'result' is a DynamoDB reserved keyword
            expr_attr_values[':result'] = result

        upload_requests_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )
        logger.info(f"Updated request {request_id} destination {destination} to status: {status}")
    except Exception as e:
        logger.error(f"Failed to update request status: {e}")


def process_instagram_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: DetailedLogger
) -> Dict[str, Any]:
    """Process Instagram posting"""
    detailed_log.log('INFO', f'Starting Instagram post for account {account_id}')

    try:
        # Get account details from DynamoDB
        detailed_log.log('INFO', 'Fetching Instagram account details from database')
        response = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        if 'Item' not in response:
            raise Exception(f"Instagram account {account_id} not found for user {user_id}")

        account = response['Item']
        detailed_log.log('INFO', f'Account details retrieved: {account.get("account_name")}')

        # Get Instagram account ID and access token
        instagram_account_id = account.get('instagram_account_id')
        access_token = account.get('access_token')

        if not instagram_account_id or not access_token:
            raise Exception("Missing Instagram account ID or access token")

        detailed_log.log('INFO', f'Instagram Business Account ID: {instagram_account_id}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Caption length: {len(caption) if caption else 0} characters')

        # Post to Instagram
        detailed_log.log('INFO', 'Calling Instagram API...')
        result = InstagramPostingService.post_reel(
            instagram_account_id=instagram_account_id,
            access_token=access_token,
            video_url=video_url,
            caption=caption
        )

        detailed_log.log('INFO', f'Instagram API returned: {json.dumps(result)}')

        return result

    except InstagramPostingError as e:
        detailed_log.log('ERROR', f'Instagram API error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise
    except Exception as e:
        detailed_log.log('ERROR', f'Unexpected error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise


def process_facebook_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: DetailedLogger
) -> Dict[str, Any]:
    """Process Facebook posting"""
    detailed_log.log('INFO', f'Starting Facebook post for account {account_id}')

    try:
        # Get account details from DynamoDB
        detailed_log.log('INFO', 'Fetching Facebook page details from database')
        detailed_log.log('INFO', f'Query key: user_id={user_id}, account_id={account_id}')
        response = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        detailed_log.log('INFO', f'DynamoDB response: {response}')

        if 'Item' not in response:
            raise Exception(f"Facebook page {account_id} not found for user {user_id}")

        account = response['Item']
        detailed_log.log('INFO', f'Page details retrieved: {account.get("account_name")}')

        # Get Page ID and access token
        page_id = account.get('page_id')
        access_token = account.get('access_token')

        if not page_id or not access_token:
            raise Exception("Missing Facebook page ID or access token")

        detailed_log.log('INFO', f'Facebook Page ID: {page_id}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Caption length: {len(caption) if caption else 0} characters')

        # Post to Facebook
        detailed_log.log('INFO', 'Calling Facebook API...')
        result = FacebookPostingService.post_video(
            page_id=page_id,
            page_access_token=access_token,
            video_url=video_url,
            caption=caption
        )

        detailed_log.log('INFO', f'Facebook API returned: {json.dumps(result)}')

        return result

    except Exception as e:
        detailed_log.log('ERROR', f'Facebook posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise


def handler(event, context):
    """
    SQS Event Handler for Async Social Media Posting

    Processes messages from the posting queue and posts to social media platforms
    """
    logger.info(f"Processing {len(event['Records'])} messages from SQS")

    for record in event['Records']:
        try:
            # Parse the message
            message = json.loads(record['body'])

            request_id = message['request_id']
            user_id = message['user_id']
            destination = message['destination']  # e.g., "instagram:account_id" or "facebook:page_id"
            video_url = message['video_url']
            caption = message.get('caption', '')

            logger.info(f"Processing request {request_id} for destination {destination}")

            # Initialize detailed logger
            detailed_log = DetailedLogger(request_id, destination)
            detailed_log.log('INFO', f'Starting async post processing')
            detailed_log.log('INFO', f'Request ID: {request_id}')
            detailed_log.log('INFO', f'User ID: {user_id}')
            detailed_log.log('INFO', f'Destination: {destination}')

            # Update status to processing
            update_request_status(request_id, destination, 'processing', detailed_log.logs)

            # Parse destination (format: "platform:account_id")
            platform, _ = destination.split(':', 1)

            # Route to appropriate posting service
            # Pass the full destination as account_id since that's what's stored in DynamoDB
            result = None
            if platform == 'instagram':
                result = process_instagram_post(
                    request_id, user_id, destination, video_url, caption, detailed_log
                )
            elif platform == 'facebook':
                result = process_facebook_post(
                    request_id, user_id, destination, video_url, caption, detailed_log
                )
            else:
                raise Exception(f"Unknown platform: {platform}")

            # Update status to success
            detailed_log.log('INFO', f'Post completed successfully')
            detailed_log.log('INFO', f'Result: {json.dumps(result)}')
            detailed_log.log('INFO', f'Summary: {json.dumps(detailed_log.get_summary())}')

            update_request_status(
                request_id,
                destination,
                'completed',
                detailed_log.logs,
                result=result
            )

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            logger.error(traceback.format_exc())

            # Update status to failed with detailed error
            try:
                error_message = str(e)
                detailed_log.log('ERROR', f'Processing failed: {error_message}')
                detailed_log.log('ERROR', f'Full traceback: {traceback.format_exc()}')

                update_request_status(
                    request_id,
                    destination,
                    'failed',
                    detailed_log.logs,
                    error=error_message
                )
            except:
                logger.error("Failed to update error status in DynamoDB")

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Processed successfully'})
    }
