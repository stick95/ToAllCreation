#!/usr/bin/env python3
"""
Check Facebook Page Access Token Permissions
"""
import requests
import json

# Your page access token
PAGE_ACCESS_TOKEN = "EAAv9uApP1u0BP4BWm9PO7QYera5L0T8zH3Ktb5CZBgrSZAQuxfMbK53bPkaWkEZALQfoBRfDP8MgRrrSdM79EcU8oZBSuc0CDeK9nOxJBlTRc89XaDQQz8WNA0T8vYc7cA0lcr9n5AN2IEnZA3rVvTgTWHQPJJoAjmIUIG1xfZA8RrkQYjKfyEZAxpUQvj8ElXHMgZDZD"

def check_token_permissions():
    """Check what permissions the token has"""

    # Debug token to see its permissions and metadata
    url = "https://graph.facebook.com/v18.0/debug_token"
    params = {
        'input_token': PAGE_ACCESS_TOKEN,
        'access_token': PAGE_ACCESS_TOKEN
    }

    print("Checking token permissions...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print("\n=== TOKEN DEBUG INFO ===")
        print(json.dumps(data, indent=2))

        token_data = data.get('data', {})
        print("\n=== TOKEN SUMMARY ===")
        print(f"App ID: {token_data.get('app_id')}")
        print(f"Type: {token_data.get('type')}")
        print(f"Valid: {token_data.get('is_valid')}")
        print(f"Expires: {token_data.get('expires_at')} ({token_data.get('data_access_expires_at')})")
        print(f"User ID: {token_data.get('user_id')}")

        scopes = token_data.get('scopes', [])
        print(f"\n=== PERMISSIONS/SCOPES ({len(scopes)}) ===")
        for scope in sorted(scopes):
            print(f"  ✓ {scope}")

        # Check for required permissions
        required = ['pages_manage_posts', 'pages_read_engagement', 'pages_show_list']
        missing = [r for r in required if r not in scopes]

        if missing:
            print(f"\n⚠️  MISSING REQUIRED PERMISSIONS:")
            for perm in missing:
                print(f"  ✗ {perm}")
        else:
            print(f"\n✅ All required permissions present!")

    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def check_page_info():
    """Get info about the page"""
    url = "https://graph.facebook.com/v18.0/872023199325243"
    params = {
        'access_token': PAGE_ACCESS_TOKEN,
        'fields': 'id,name,category,can_post,access_token'
    }

    print("\n\n=== PAGE INFO ===")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def check_video_upload_limits():
    """Check if we can upload videos"""
    url = "https://graph.facebook.com/v18.0/872023199325243"
    params = {
        'access_token': PAGE_ACCESS_TOKEN,
        'fields': 'id,name,can_post,tasks'
    }

    print("\n\n=== PAGE TASKS/CAPABILITIES ===")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    check_token_permissions()
    check_page_info()
    check_video_upload_limits()
