"""
Upload Requests Management
Handles creation, retrieval, and tracking of async upload requests
"""
import os
import uuid
import json
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

upload_requests_table = dynamodb.Table(os.environ['UPLOAD_REQUESTS_TABLE'])
posting_queue_url = os.environ['POSTING_QUEUE_URL']


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def create_upload_request(
    user_id: str,
    video_url: str,
    caption: str,
    destinations: List[str],
    tiktok_settings: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Create a new upload request and queue posting jobs

    Args:
        user_id: User ID
        video_url: S3 URL of the video
        caption: Post caption
        destinations: List of destination identifiers (e.g., ["instagram:account_id", "facebook:page_id"])
        tiktok_settings: Optional TikTok-specific settings (privacy, duet, comments, etc.)

    Returns:
        Upload request details including request_id
    """
    # Generate request ID
    request_id = str(uuid.uuid4())
    now = datetime.utcnow()
    timestamp = int(now.timestamp())

    # Initialize destinations status
    destinations_status = {}
    for dest in destinations:
        destinations_status[dest] = {
            'status': 'queued',
            'created_at': now.isoformat(),
            'updated_at': now.isoformat(),
            'logs': []
        }

    # Create request record
    request_item = {
        'request_id': request_id,
        'user_id': user_id,
        'video_url': video_url,
        'caption': caption,
        'destinations': destinations_status,
        'created_at': timestamp,
        'updated_at': timestamp,
        'status': 'queued',  # Overall status
        'ttl': int((now + timedelta(days=90)).timestamp())  # Auto-delete after 90 days
    }

    # Save to DynamoDB
    upload_requests_table.put_item(Item=request_item)

    # Queue posting jobs for each destination
    for dest in destinations:
        message = {
            'request_id': request_id,
            'user_id': user_id,
            'destination': dest,
            'video_url': video_url,
            'caption': caption
        }

        # Add TikTok settings if provided and destination is TikTok
        if tiktok_settings and dest.startswith('tiktok:'):
            message['tiktok_settings'] = tiktok_settings

        # Send message to SQS
        message_params = {
            'QueueUrl': posting_queue_url,
            'MessageBody': json.dumps(message)
        }

        # Only add MessageGroupId for FIFO queues
        if '.fifo' in posting_queue_url.lower():
            message_params['MessageGroupId'] = request_id

        sqs.send_message(**message_params)

    return request_item


def get_upload_request(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific upload request by ID

    Args:
        request_id: Request ID

    Returns:
        Upload request details or None if not found
    """
    response = upload_requests_table.get_item(
        Key={'request_id': request_id}
    )

    return response.get('Item')


def list_upload_requests(
    user_id: str,
    limit: int = 50,
    last_evaluated_key: Dict = None
) -> Dict[str, Any]:
    """
    List upload requests for a user

    Args:
        user_id: User ID
        limit: Maximum number of requests to return
        last_evaluated_key: Pagination token

    Returns:
        Dict with 'requests' list and optional 'last_evaluated_key'
    """
    query_params = {
        'IndexName': 'user_id-created_at-index',
        'KeyConditionExpression': '#user_id = :user_id',
        'ExpressionAttributeNames': {
            '#user_id': 'user_id'
        },
        'ExpressionAttributeValues': {
            ':user_id': user_id
        },
        'ScanIndexForward': False,  # Sort by created_at descending (newest first)
        'Limit': limit
    }

    if last_evaluated_key:
        query_params['ExclusiveStartKey'] = last_evaluated_key

    response = upload_requests_table.query(**query_params)

    result = {
        'requests': response['Items']
    }

    if 'LastEvaluatedKey' in response:
        result['last_evaluated_key'] = response['LastEvaluatedKey']

    return result


def get_request_logs(request_id: str, destination: Optional[str] = None) -> Dict[str, Any]:
    """
    Get detailed logs for a request

    Args:
        request_id: Request ID
        destination: Optional specific destination to get logs for

    Returns:
        Dict with logs and metadata
    """
    request = get_upload_request(request_id)

    if not request:
        return {
            'error': 'Request not found',
            'request_id': request_id
        }

    if destination:
        # Get logs for specific destination
        dest_data = request.get('destinations', {}).get(destination, {})
        return {
            'request_id': request_id,
            'destination': destination,
            'status': dest_data.get('status'),
            'logs': dest_data.get('logs', []),
            'error': dest_data.get('error'),
            'result': dest_data.get('result'),
            'created_at': dest_data.get('created_at'),
            'updated_at': dest_data.get('updated_at')
        }
    else:
        # Get all destination logs
        destinations_logs = {}
        for dest, dest_data in request.get('destinations', {}).items():
            destinations_logs[dest] = {
                'status': dest_data.get('status'),
                'logs': dest_data.get('logs', []),
                'error': dest_data.get('error'),
                'result': dest_data.get('result'),
                'created_at': dest_data.get('created_at'),
                'updated_at': dest_data.get('updated_at')
            }

        return {
            'request_id': request_id,
            'overall_status': request.get('status'),
            'destinations': destinations_logs,
            'created_at': request.get('created_at'),
            'video_url': request.get('video_url'),
            'caption': request.get('caption')
        }


def update_overall_status(request_id: str):
    """
    Update the overall status of a request based on destination statuses

    Status priority: failed > processing > queued > completed
    """
    request = get_upload_request(request_id)
    if not request:
        return

    destinations = request.get('destinations', {})
    if not destinations:
        return

    # Collect all statuses
    statuses = [dest.get('status') for dest in destinations.values()]

    # Determine overall status
    if any(s == 'failed' for s in statuses):
        overall_status = 'failed'
    elif any(s == 'processing' for s in statuses):
        overall_status = 'processing'
    elif any(s == 'queued' for s in statuses):
        overall_status = 'queued'
    elif all(s == 'completed' for s in statuses):
        overall_status = 'completed'
    else:
        overall_status = 'processing'

    # Update if different
    if request.get('status') != overall_status:
        upload_requests_table.update_item(
            Key={'request_id': request_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': overall_status,
                ':updated_at': int(datetime.utcnow().timestamp())
            }
        )


def resubmit_failed_destination(request_id: str, destination: str) -> Dict[str, Any]:
    """
    Resubmit a failed posting task for a specific destination

    Args:
        request_id: Request ID
        destination: Destination to resubmit (e.g., "instagram:account_id")

    Returns:
        Dict with success message

    Raises:
        ValueError: If request not found, destination not found, or not in failed state
    """
    # Get the upload request
    request = get_upload_request(request_id)

    if not request:
        raise ValueError("Upload request not found")

    # Verify destination exists and is failed
    destinations = request.get('destinations', {})
    if destination not in destinations:
        raise ValueError("Destination not found")

    dest_data = destinations[destination]
    if dest_data.get('status') != 'failed':
        raise ValueError("Only failed tasks can be resubmitted")

    # Get video URL and caption from the request
    video_url = request.get('video_url')
    caption = request.get('caption', '')
    user_id = request.get('user_id')

    # Update destination status to queued
    now = datetime.utcnow()
    upload_requests_table.update_item(
        Key={'request_id': request_id},
        UpdateExpression='SET destinations.#dest.#status = :status, destinations.#dest.updated_at = :updated_at, destinations.#dest.logs = :logs REMOVE destinations.#dest.#error',
        ExpressionAttributeNames={
            '#dest': destination,
            '#status': 'status',
            '#error': 'error'
        },
        ExpressionAttributeValues={
            ':status': 'queued',
            ':updated_at': now.isoformat(),
            ':logs': [{
                'timestamp': now.isoformat(),
                'level': 'INFO',
                'message': 'Task resubmitted by user'
            }]
        }
    )

    # Send message to SQS queue to reprocess
    message_body = {
        'request_id': request_id,
        'user_id': user_id,
        'destination': destination,
        'video_url': video_url,
        'caption': caption
    }

    sqs.send_message(
        QueueUrl=posting_queue_url,
        MessageBody=json.dumps(message_body)
    )

    # Update overall status
    update_overall_status(request_id)

    return {
        'message': 'Task resubmitted successfully',
        'request_id': request_id,
        'destination': destination
    }
