"""
Async Worker for Social Media Posting
Processes SQS messages to post content to social media platforms
"""
import json
import logging
import os
import traceback
import time
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError

# Import posting services
from instagram_posting import InstagramPostingService, InstagramPostingError
from facebook_posting import FacebookPostingService
from twitter_posting import TwitterPostingService, TwitterPostingError
from linkedin_posting import LinkedInPostingService, LinkedInPostingError
from tiktok_posting import TikTokPostingService, TikTokPostingError

# Import OAuth handlers for token refresh
from oauth.tiktok_handler import TikTokOAuthHandler
from oauth.linkedin_handler import LinkedInOAuthHandler
from oauth.facebook_handler import FacebookOAuthHandler

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


def update_parent_request_status(request_id: str):
    """
    Update the parent request's overall status based on destination statuses

    Logic:
    - "processing" if any destination is processing
    - "failed" if any destination has failed
    - "completed" if all destinations are completed
    - "queued" if no destinations have started yet
    """
    try:
        # Get current request data
        response = upload_requests_table.get_item(Key={'request_id': request_id})

        if 'Item' not in response:
            logger.error(f"Request {request_id} not found")
            return

        request = response['Item']
        destinations = request.get('destinations', {})

        if not destinations:
            logger.warning(f"No destinations found for request {request_id}")
            return

        # Count status types
        statuses = [dest.get('status', 'queued') for dest in destinations.values()]
        has_processing = 'processing' in statuses
        has_failed = 'failed' in statuses
        all_completed = all(s == 'completed' for s in statuses)

        # Determine overall status
        if has_processing:
            overall_status = 'processing'
        elif has_failed:
            overall_status = 'failed'
        elif all_completed:
            overall_status = 'completed'
        else:
            overall_status = 'queued'

        # Update parent status
        upload_requests_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': overall_status,
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Updated parent request {request_id} status to: {overall_status}")

    except Exception as e:
        logger.error(f"Failed to update parent request status: {e}")


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

        # Update parent request status based on all destinations
        update_parent_request_status(request_id)

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
        token_expires_at = int(account.get('token_expires_at', 0))

        if not instagram_account_id or not access_token:
            raise Exception("Missing Instagram account ID or access token")

        # Check if token is expired or expiring soon (within 7 days for Meta tokens)
        current_time = int(time.time())
        if token_expires_at and current_time >= (token_expires_at - 604800):  # 7 days = 604800 seconds
            detailed_log.log('INFO', f'Access token expired or expiring soon (expires at {token_expires_at}, current {current_time})')
            detailed_log.log('INFO', 'Refreshing Instagram/Facebook access token...')
            try:
                facebook_handler = FacebookOAuthHandler()
                new_tokens = facebook_handler.refresh_access_token(access_token)

                # Update token in database
                new_expires_at = int(time.time()) + new_tokens.expires_in
                social_accounts_table.update_item(
                    Key={
                        'user_id': user_id,
                        'account_id': account_id
                    },
                    UpdateExpression='SET access_token = :token, token_expires_at = :expires, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':token': new_tokens.access_token,
                        ':expires': new_expires_at,
                        ':updated': int(time.time())
                    }
                )
                access_token = new_tokens.access_token
                detailed_log.log('INFO', f'Token refreshed successfully. New expiration: {new_expires_at}')
            except Exception as e:
                detailed_log.log('ERROR', f'Failed to refresh token: {str(e)}')
                raise Exception(f"Failed to refresh Instagram/Facebook token: {str(e)}")

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
        token_expires_at = int(account.get('token_expires_at', 0))

        if not page_id or not access_token:
            raise Exception("Missing Facebook page ID or access token")

        # Check if token is expired or expiring soon (within 7 days for Meta tokens)
        current_time = int(time.time())
        if token_expires_at and current_time >= (token_expires_at - 604800):  # 7 days = 604800 seconds
            detailed_log.log('INFO', f'Access token expired or expiring soon (expires at {token_expires_at}, current {current_time})')
            detailed_log.log('INFO', 'Refreshing Facebook access token...')
            try:
                facebook_handler = FacebookOAuthHandler()
                new_tokens = facebook_handler.refresh_access_token(access_token)

                # Update token in database
                new_expires_at = int(time.time()) + new_tokens.expires_in
                social_accounts_table.update_item(
                    Key={
                        'user_id': user_id,
                        'account_id': account_id
                    },
                    UpdateExpression='SET access_token = :token, token_expires_at = :expires, updated_at = :updated',
                    ExpressionAttributeValues={
                        ':token': new_tokens.access_token,
                        ':expires': new_expires_at,
                        ':updated': int(time.time())
                    }
                )
                access_token = new_tokens.access_token
                detailed_log.log('INFO', f'Token refreshed successfully. New expiration: {new_expires_at}')
            except Exception as e:
                detailed_log.log('ERROR', f'Failed to refresh token: {str(e)}')
                raise Exception(f"Failed to refresh Facebook token: {str(e)}")

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


def process_twitter_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: DetailedLogger
) -> Dict[str, Any]:
    """Process Twitter posting"""
    detailed_log.log('INFO', f'Starting Twitter post for account {account_id}')

    try:
        # Get account details from DynamoDB
        detailed_log.log('INFO', 'Fetching Twitter account details from database')
        detailed_log.log('INFO', f'Query key: user_id={user_id}, account_id={account_id}')
        response = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        detailed_log.log('INFO', f'DynamoDB response: {response}')

        if 'Item' not in response:
            raise Exception(f"Twitter account {account_id} not found for user {user_id}")

        account = response['Item']
        detailed_log.log('INFO', f'Account details retrieved: {account.get("username")}')

        # Get OAuth credentials
        oauth2_access_token = account.get('access_token')  # OAuth 2.0 for tweet creation
        oauth1_access_token_secret = account.get('refresh_token')  # Using refresh_token field to store OAuth 1.0a token secret
        twitter_user_id = account.get('platform_user_id')

        if not oauth2_access_token:
            raise Exception("Missing Twitter OAuth 2.0 access token")

        # Get OAuth 1.0a credentials from environment
        api_key = os.environ.get('TWITTER_API_KEY')
        api_secret = os.environ.get('TWITTER_API_SECRET')

        if not api_key or not api_secret:
            raise Exception("Missing Twitter OAuth 1.0a credentials (API Key/Secret)")

        detailed_log.log('INFO', f'Twitter User ID: {twitter_user_id}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Tweet text length: {len(caption) if caption else 0} characters')

        # Post to Twitter (using both OAuth 1.0a for media upload and OAuth 2.0 for tweet creation)
        detailed_log.log('INFO', 'Calling Twitter API...')
        result = TwitterPostingService.post_video(
            access_token=oauth2_access_token,
            video_url=video_url,
            text=caption,
            user_id=twitter_user_id,
            api_key=api_key,
            api_secret=api_secret,
            access_token_secret=oauth1_access_token_secret
        )

        detailed_log.log('INFO', f'Twitter API returned: {json.dumps(result)}')

        return result

    except TwitterPostingError as e:
        detailed_log.log('ERROR', f'Twitter posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise
    except Exception as e:
        detailed_log.log('ERROR', f'Twitter posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise


def process_youtube_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: 'DetailedLogger'
):
    """
    Process YouTube video posting

    Args:
        request_id: Unique request ID
        user_id: Cognito user ID
        account_id: Account ID (format: "youtube:channel_id")
        video_url: S3 URL to video
        caption: Video caption/title
        detailed_log: Detailed logger instance
    """
    try:
        import time
        from youtube_posting import YouTubePostingService, YouTubePostingError
        from oauth_token_exchange import YouTubeTokenExchange

        detailed_log.log('INFO', f'Starting YouTube post for account {account_id}')

        # Get YouTube account details
        detailed_log.log('INFO', f'Fetching YouTube account details from database')
        detailed_log.log('INFO', f'Query key: user_id={user_id}, account_id={account_id}')

        account = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        detailed_log.log('INFO', f'DynamoDB response: {account}')

        if 'Item' not in account:
            raise Exception(f"YouTube account {account_id} not found")

        account_data = account['Item']
        detailed_log.log('INFO', f'Account details retrieved: {account_data.get("username")}')

        access_token = account_data['access_token']
        refresh_token = account_data.get('refresh_token')
        token_expires_at = account_data.get('token_expires_at')
        channel_id = account_data['platform_user_id']

        detailed_log.log('INFO', f'YouTube Channel ID: {channel_id}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Caption length: {len(caption)} characters')

        # Check if token needs refresh
        current_time = int(time.time())
        if token_expires_at and current_time >= token_expires_at:
            detailed_log.log('INFO', 'Access token expired, refreshing...')

            client_id = os.environ.get('YOUTUBE_CLIENT_ID')
            # YouTube client secret is stored in SSM Parameter Store (SecureString)
            from ssm_helper import get_youtube_client_secret
            client_secret = get_youtube_client_secret()

            if not refresh_token:
                raise Exception("No refresh token available for YouTube account")

            # Refresh the access token
            token_data = YouTubeTokenExchange.refresh_token(
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret
            )

            access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            new_token_expires_at = int(time.time()) + expires_in

            # Update token in database
            social_accounts_table.update_item(
                Key={
                    'user_id': user_id,
                    'account_id': account_id
                },
                UpdateExpression='SET access_token = :token, token_expires_at = :expires, updated_at = :updated',
                ExpressionAttributeValues={
                    ':token': access_token,
                    ':expires': new_token_expires_at,
                    ':updated': current_time
                }
            )

            detailed_log.log('INFO', 'Access token refreshed successfully')

        # Post to YouTube
        detailed_log.log('INFO', 'Calling YouTube API...')
        result = YouTubePostingService.post_video(
            access_token=access_token,
            video_url=video_url,
            title=caption[:100] if caption else "Untitled Short",  # YouTube Shorts title limit
            description=caption,
            privacy_status="public"
        )

        detailed_log.log('INFO', f'YouTube API returned: {json.dumps(result)}')

        return result

    except YouTubePostingError as e:
        detailed_log.log('ERROR', f'YouTube posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise
    except Exception as e:
        detailed_log.log('ERROR', f'YouTube posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise


def process_linkedin_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: 'DetailedLogger'
):
    """
    Process LinkedIn video posting

    Args:
        request_id: Unique request ID
        user_id: Cognito user ID
        account_id: Account ID (format: "linkedin:person_id")
        video_url: S3 URL to video
        caption: Video caption/text
        detailed_log: Detailed logger instance
    """
    try:
        detailed_log.log('INFO', f'Starting LinkedIn post for account {account_id}')

        # Get LinkedIn account details
        detailed_log.log('INFO', f'Fetching LinkedIn account details from database')
        detailed_log.log('INFO', f'Query key: user_id={user_id}, account_id={account_id}')

        account = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        detailed_log.log('INFO', f'DynamoDB response: {account}')

        if 'Item' not in account:
            raise Exception(f"LinkedIn account {account_id} not found")

        account_data = account['Item']
        detailed_log.log('INFO', f'Account details retrieved: {account_data.get("username")}')

        access_token = account_data['access_token']
        refresh_token = account_data.get('refresh_token')
        token_expires_at = int(account_data.get('token_expires_at', 0))
        person_id = account_data['platform_user_id']
        person_urn = f"urn:li:person:{person_id}"

        # Check if token is expired or expiring soon (within 7 days for LinkedIn tokens)
        current_time = int(time.time())
        if token_expires_at and current_time >= (token_expires_at - 604800):  # 7 days = 604800 seconds
            detailed_log.log('INFO', f'Access token expired or expiring soon (expires at {token_expires_at}, current {current_time})')
            if refresh_token:
                detailed_log.log('INFO', 'Refreshing LinkedIn access token...')
                try:
                    linkedin_handler = LinkedInOAuthHandler()
                    new_tokens = linkedin_handler.refresh_access_token(refresh_token)

                    # Update token in database
                    new_expires_at = int(time.time()) + new_tokens.expires_in
                    social_accounts_table.update_item(
                        Key={
                            'user_id': user_id,
                            'account_id': account_id
                        },
                        UpdateExpression='SET access_token = :token, refresh_token = :refresh, token_expires_at = :expires, updated_at = :updated',
                        ExpressionAttributeValues={
                            ':token': new_tokens.access_token,
                            ':refresh': new_tokens.refresh_token,
                            ':expires': new_expires_at,
                            ':updated': int(time.time())
                        }
                    )
                    access_token = new_tokens.access_token
                    detailed_log.log('INFO', f'Token refreshed successfully. New expiration: {new_expires_at}')
                except Exception as e:
                    detailed_log.log('ERROR', f'Failed to refresh token: {str(e)}')
                    raise Exception(f"Failed to refresh LinkedIn token: {str(e)}")
            else:
                raise Exception("Access token expired and no refresh token available")

        detailed_log.log('INFO', f'LinkedIn Person URN: {person_urn}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Caption length: {len(caption)} characters')

        # Post video to LinkedIn
        detailed_log.log('INFO', 'Calling LinkedIn API...')
        result = LinkedInPostingService.post_video(
            person_urn=person_urn,
            access_token=access_token,
            video_url=video_url,
            caption=caption
        )

        detailed_log.log('INFO', f'LinkedIn API returned: {json.dumps(result)}')

        return result

    except LinkedInPostingError as e:
        detailed_log.log('ERROR', f'LinkedIn posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise
    except Exception as e:
        detailed_log.log('ERROR', f'LinkedIn posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise


def process_tiktok_post(
    request_id: str,
    user_id: str,
    account_id: str,
    video_url: str,
    caption: str,
    detailed_log: 'DetailedLogger'
):
    """
    Process TikTok video posting

    Args:
        request_id: Unique request ID
        user_id: Cognito user ID
        account_id: Account ID (format: "tiktok:open_id")
        video_url: S3 URL to video
        caption: Video caption/text
        detailed_log: Detailed logger instance
    """
    try:
        detailed_log.log('INFO', f'Starting TikTok post for account {account_id}')

        # Get TikTok account details
        detailed_log.log('INFO', f'Fetching TikTok account details from database')
        detailed_log.log('INFO', f'Query key: user_id={user_id}, account_id={account_id}')

        account = social_accounts_table.get_item(
            Key={
                'user_id': user_id,
                'account_id': account_id
            }
        )

        detailed_log.log('INFO', f'DynamoDB response: {account}')

        if 'Item' not in account:
            raise Exception(f"TikTok account {account_id} not found")

        account_data = account['Item']
        detailed_log.log('INFO', f'Account details retrieved: {account_data.get("username")}')

        access_token = account_data['access_token']
        refresh_token = account_data.get('refresh_token')
        token_expires_at = int(account_data.get('token_expires_at', 0))
        open_id = account_data['platform_user_id']

        # Check if token is expired or about to expire (within 5 minutes)
        current_time = int(time.time())
        if token_expires_at and current_time >= (token_expires_at - 300):
            detailed_log.log('INFO', f'Access token expired or expiring soon (expires at {token_expires_at}, current {current_time})')
            if refresh_token:
                detailed_log.log('INFO', 'Refreshing TikTok access token...')
                try:
                    tiktok_handler = TikTokOAuthHandler()
                    new_tokens = tiktok_handler.refresh_access_token(refresh_token)

                    # Update token in database
                    new_expires_at = int(time.time()) + new_tokens.expires_in
                    social_accounts_table.update_item(
                        Key={
                            'user_id': user_id,
                            'account_id': account_id
                        },
                        UpdateExpression='SET access_token = :token, refresh_token = :refresh, token_expires_at = :expires',
                        ExpressionAttributeValues={
                            ':token': new_tokens.access_token,
                            ':refresh': new_tokens.refresh_token,
                            ':expires': new_expires_at
                        }
                    )
                    access_token = new_tokens.access_token
                    detailed_log.log('INFO', f'Token refreshed successfully. New expiration: {new_expires_at}')
                except Exception as e:
                    detailed_log.log('ERROR', f'Failed to refresh token: {str(e)}')
                    raise Exception(f"Failed to refresh TikTok token: {str(e)}")
            else:
                raise Exception("Access token expired and no refresh token available")

        detailed_log.log('INFO', f'TikTok Open ID: {open_id}')
        detailed_log.log('INFO', f'Video URL: {video_url}')
        detailed_log.log('INFO', f'Caption length: {len(caption)} characters')

        # Post video to TikTok
        detailed_log.log('INFO', 'Calling TikTok API...')
        result = TikTokPostingService.post_video(
            open_id=open_id,
            access_token=access_token,
            video_url=video_url,
            caption=caption
        )

        detailed_log.log('INFO', f'TikTok API returned: {json.dumps(result)}')

        return result

    except TikTokPostingError as e:
        detailed_log.log('ERROR', f'TikTok posting error: {str(e)}')
        detailed_log.log('ERROR', f'Traceback: {traceback.format_exc()}')
        raise
    except Exception as e:
        detailed_log.log('ERROR', f'TikTok posting error: {str(e)}')
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
            elif platform == 'twitter':
                result = process_twitter_post(
                    request_id, user_id, destination, video_url, caption, detailed_log
                )
            elif platform == 'youtube':
                result = process_youtube_post(
                    request_id, user_id, destination, video_url, caption, detailed_log
                )
            elif platform == 'linkedin':
                result = process_linkedin_post(
                    request_id, user_id, destination, video_url, caption, detailed_log
                )
            elif platform == 'tiktok':
                result = process_tiktok_post(
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
