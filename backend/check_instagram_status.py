#!/usr/bin/env python3
"""
Check Instagram container status
"""
import requests
import sys

# Your most recent container ID from the logs
container_id = "17845684935610547"

# Access token from your Instagram account
access_token = "EAAv9uApP1u0BP6WRWTHZA9fbY3dTHK2MTEupECTLMRfvUYtvIOx3x31mIrzBQCc0SJQM4gLeTy11bvRTaP48XHLRSZBqfcc8ITifqslOaY5ZCrugfSZA2x8wZBm37q94EiZCsNhZCaE6fJEvORFpR9iS7DCYhh8aYWXn87sZACue70JQEQT2IM7fLxyIkrz7ZBl0GGQZDZD"

# Check status
url = f"https://graph.facebook.com/v18.0/{container_id}"
params = {
    'access_token': access_token,
    'fields': 'status_code,id,status'  # Added 'status' field for error details
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print(f"Container ID: {container_id}")
    print(f"Status Code: {data.get('status_code', 'UNKNOWN')}")

    # Print full response for debugging
    print(f"\nFull response:")
    import json
    print(json.dumps(data, indent=2))

    status = data.get('status_code')
    if status == 'FINISHED':
        print("\n✅ Video is ready! You can now publish it.")
        print("\nTo publish, run:")
        print(f"  POST https://graph.facebook.com/v18.0/17841478316398194/media_publish")
        print(f"  Params: creation_id={container_id}, access_token=...")
    elif status == 'IN_PROGRESS':
        print("\n⏳ Video is still processing. Check again in a minute.")
    elif status == 'ERROR':
        print("\n❌ Instagram reported an error processing the video")
        # Check if there's a status field with error details
        if 'status' in data:
            print(f"Error details: {data['status']}")
    elif status == 'PUBLISHED':
        print("\n✅ Video has already been published!")
else:
    print(f"Error checking status: {response.status_code}")
    print(response.text)
