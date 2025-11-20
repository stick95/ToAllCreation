#!/usr/bin/env python3
"""
Resubmit failed upload requests to SQS for reprocessing
"""
import boto3
import json
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
sqs = boto3.client('sqs', region_name='us-west-2')

UPLOAD_REQUESTS_TABLE = 'toallcreation-upload-requests'
QUEUE_URL = 'https://sqs.us-west-2.amazonaws.com/271297706586/toallcreation-posting-queue'

def get_failed_requests(user_id: str = None, limit: int = 10):
    """Get upload requests with failed destinations from DynamoDB"""
    table = dynamodb.Table(UPLOAD_REQUESTS_TABLE)

    if user_id:
        # Scan for specific user's requests
        response = table.scan(
            FilterExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=limit
        )
    else:
        # Scan all requests
        response = table.scan(Limit=limit)

    # Filter for requests that have at least one failed destination
    items = response.get('Items', [])
    failed_requests = []

    for item in items:
        destinations = item.get('destinations', {})
        has_failed = any(
            dest_data.get('status') == 'failed'
            for dest_data in destinations.values()
        )
        if has_failed:
            failed_requests.append(item)

    return failed_requests

def resubmit_request(request):
    """Resubmit a failed request to SQS"""
    request_id = request['request_id']
    user_id = request['user_id']
    video_url = request['video_url']
    caption = request.get('caption', '')

    # Find failed destinations
    destinations = request.get('destinations', {})
    resubmitted = []

    for dest_key, dest_data in destinations.items():
        if dest_data.get('status') == 'failed':
            # Create SQS message
            message = {
                'request_id': request_id,
                'user_id': user_id,
                'destination': dest_key,
                'video_url': video_url,
                'caption': caption
            }

            # Send to SQS
            response = sqs.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=json.dumps(message)
            )

            resubmitted.append(dest_key)
            print(f"  ✓ Resubmitted {dest_key}: MessageId={response['MessageId']}")

    return resubmitted

def main():
    import sys

    # Get user_id from command line if provided
    user_id = sys.argv[1] if len(sys.argv) > 1 else None

    print(f"Looking for failed requests{' for user ' + user_id if user_id else ''}...")

    failed_requests = get_failed_requests(user_id, limit=50)

    if not failed_requests:
        print("No failed requests found.")
        return

    print(f"\nFound {len(failed_requests)} failed request(s):\n")

    for request in failed_requests:
        request_id = request['request_id']
        video_url = request['video_url']
        created_at = request['created_at']

        print(f"Request: {request_id}")
        print(f"  Video: {video_url}")
        print(f"  Created: {created_at}")

        # Show failed destinations
        destinations = request.get('destinations', {})
        failed_dests = [k for k, v in destinations.items() if v.get('status') == 'failed']
        print(f"  Failed destinations: {', '.join(failed_dests)}")

        # Ask to resubmit
        answer = input(f"  Resubmit? (y/n): ").lower()
        if answer == 'y':
            resubmitted = resubmit_request(request)
            print(f"  → Resubmitted {len(resubmitted)} destination(s)\n")
        else:
            print("  → Skipped\n")

if __name__ == '__main__':
    main()
