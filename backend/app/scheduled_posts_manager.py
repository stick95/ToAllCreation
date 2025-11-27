"""
Scheduled Posts Management
Handles creation, retrieval, and management of scheduled social media posts
"""
import os
import uuid
import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal


# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

scheduled_posts_table = dynamodb.Table(os.environ.get('SCHEDULED_POSTS_TABLE', 'toallcreation-scheduled-posts'))


def create_scheduled_post(
    user_id: str,
    video_url: str,
    caption: str,
    destinations: List[str],
    scheduled_time: int,
    timezone: str = "UTC"
) -> Dict[str, Any]:
    """
    Create a new scheduled post

    Args:
        user_id: User ID
        video_url: S3 URL of the video
        caption: Post caption
        destinations: List of destination identifiers
        scheduled_time: Unix timestamp when to post
        timezone: User's timezone (for display purposes)

    Returns:
        Scheduled post details
    """
    scheduled_post_id = str(uuid.uuid4())
    now = datetime.utcnow()
    timestamp = int(now.timestamp())

    # Validate scheduled time is in the future
    if scheduled_time <= timestamp:
        raise ValueError("Scheduled time must be in the future")

    scheduled_post = {
        'scheduled_post_id': scheduled_post_id,
        'user_id': user_id,
        'video_url': video_url,
        'caption': caption,
        'destinations': destinations,
        'scheduled_time': scheduled_time,
        'timezone': timezone,
        'status': 'scheduled',
        'created_at': timestamp,
        'updated_at': timestamp,
        'ttl': int((now + timedelta(days=90)).timestamp())  # Auto-delete after 90 days
    }

    scheduled_posts_table.put_item(Item=scheduled_post)

    return scheduled_post


def get_scheduled_post(user_id: str, scheduled_post_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific scheduled post

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID

    Returns:
        Scheduled post details or None if not found
    """
    response = scheduled_posts_table.get_item(
        Key={
            'user_id': user_id,
            'scheduled_post_id': scheduled_post_id
        }
    )

    return response.get('Item')


def list_scheduled_posts(
    user_id: str,
    limit: int = 50,
    last_evaluated_key: Dict = None
) -> Dict[str, Any]:
    """
    List scheduled posts for a user

    Args:
        user_id: User ID
        limit: Maximum number of posts to return
        last_evaluated_key: Pagination token

    Returns:
        Dict with 'posts' list and optional 'last_evaluated_key'
    """
    query_params = {
        'KeyConditionExpression': '#user_id = :user_id',
        'ExpressionAttributeNames': {
            '#user_id': 'user_id'
        },
        'ExpressionAttributeValues': {
            ':user_id': user_id
        },
        'ScanIndexForward': False,  # Newest first
        'Limit': limit
    }

    if last_evaluated_key:
        query_params['ExclusiveStartKey'] = last_evaluated_key

    response = scheduled_posts_table.query(**query_params)

    result = {
        'posts': response['Items']
    }

    if 'LastEvaluatedKey' in response:
        result['last_evaluated_key'] = response['LastEvaluatedKey']

    return result


def update_scheduled_post(
    user_id: str,
    scheduled_post_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update a scheduled post

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID
        updates: Dict of fields to update (scheduled_time, caption, destinations)

    Returns:
        Updated scheduled post
    """
    # Build update expression
    update_parts = []
    attr_names = {}
    attr_values = {}

    allowed_updates = ['scheduled_time', 'caption', 'destinations', 'timezone']

    for key, value in updates.items():
        if key in allowed_updates:
            update_parts.append(f'#{key} = :{key}')
            attr_names[f'#{key}'] = key
            attr_values[f':{key}'] = value

    # Always update updated_at
    update_parts.append('#updated_at = :updated_at')
    attr_names['#updated_at'] = 'updated_at'
    attr_values[':updated_at'] = int(datetime.utcnow().timestamp())

    if not update_parts:
        raise ValueError("No valid updates provided")

    update_expression = 'SET ' + ', '.join(update_parts)

    response = scheduled_posts_table.update_item(
        Key={
            'user_id': user_id,
            'scheduled_post_id': scheduled_post_id
        },
        UpdateExpression=update_expression,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues='ALL_NEW'
    )

    return response['Attributes']


def cancel_scheduled_post(user_id: str, scheduled_post_id: str) -> Dict[str, Any]:
    """
    Cancel a scheduled post

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID

    Returns:
        Updated scheduled post with cancelled status
    """
    response = scheduled_posts_table.update_item(
        Key={
            'user_id': user_id,
            'scheduled_post_id': scheduled_post_id
        },
        UpdateExpression='SET #status = :status, updated_at = :updated_at',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': 'cancelled',
            ':updated_at': int(datetime.utcnow().timestamp())
        },
        ReturnValues='ALL_NEW'
    )

    return response['Attributes']


def get_posts_ready_to_publish() -> List[Dict[str, Any]]:
    """
    Get all scheduled posts ready to be published (status='scheduled' and scheduled_time <= now)

    Returns:
        List of scheduled posts ready to publish
    """
    now = int(datetime.utcnow().timestamp())

    response = scheduled_posts_table.query(
        IndexName='scheduled_time-index',
        KeyConditionExpression='#status = :status AND scheduled_time <= :now',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': 'scheduled',
            ':now': now
        }
    )

    return response['Items']


def mark_post_as_processing(user_id: str, scheduled_post_id: str) -> bool:
    """
    Atomically mark a scheduled post as processing only if status is 'scheduled'
    Prevents race conditions when multiple scheduler executions run simultaneously

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID

    Returns:
        True if successfully marked as processing, False if already processing/posted
    """
    try:
        scheduled_posts_table.update_item(
            Key={
                'user_id': user_id,
                'scheduled_post_id': scheduled_post_id
            },
            UpdateExpression='SET #status = :processing, updated_at = :updated_at',
            ConditionExpression='#status = :scheduled',  # Only update if still scheduled
            ExpressionAttributeNames={
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':processing': 'processing',
                ':scheduled': 'scheduled',
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Post is already being processed or was processed
            return False
        raise  # Re-raise other errors


def mark_post_as_posted(user_id: str, scheduled_post_id: str, request_id: str) -> None:
    """
    Mark a scheduled post as successfully posted

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID
        request_id: Upload request ID that was created
    """
    now = int(datetime.utcnow().timestamp())

    scheduled_posts_table.update_item(
        Key={
            'user_id': user_id,
            'scheduled_post_id': scheduled_post_id
        },
        UpdateExpression='SET #status = :status, updated_at = :updated_at, posted_at = :posted_at, request_id = :request_id',
        ExpressionAttributeNames={
            '#status': 'status'
        },
        ExpressionAttributeValues={
            ':status': 'posted',
            ':updated_at': now,
            ':posted_at': now,
            ':request_id': request_id
        }
    )


def mark_post_as_failed(user_id: str, scheduled_post_id: str, error: str) -> None:
    """
    Mark a scheduled post as failed

    Args:
        user_id: User ID
        scheduled_post_id: Scheduled post ID
        error: Error message
    """
    scheduled_posts_table.update_item(
        Key={
            'user_id': user_id,
            'scheduled_post_id': scheduled_post_id
        },
        UpdateExpression='SET #status = :status, updated_at = :updated_at, #error = :error',
        ExpressionAttributeNames={
            '#status': 'status',
            '#error': 'error'
        },
        ExpressionAttributeValues={
            ':status': 'failed',
            ':updated_at': int(datetime.utcnow().timestamp()),
            ':error': error
        }
    )
