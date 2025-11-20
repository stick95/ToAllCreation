#!/usr/bin/env python3
"""
Check Facebook/Instagram API permissions
"""
import requests

# Access token
access_token = "EAAv9uApP1u0BP6WRWTHZA9fbY3dTHK2MTEupECTLMRfvUYtvIOx3x31mIrzBQCc0SJQM4gLeTy11bvRTaP48XHLRSZBqfcc8ITifqslOaY5ZCrugfSZA2x8wZBm37q94EiZCsNhZCaE6fJEvORFpR9iS7DCYhh8aYWXn87sZACue70JQEQT2IM7fLxyIkrz7ZBl0GGQZDZD"

# Check token permissions
url = "https://graph.facebook.com/v18.0/me/permissions"
params = {'access_token': access_token}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    print("Current permissions:")
    print("-" * 50)
    for perm in data.get('data', []):
        status = perm.get('status')
        permission = perm.get('permission')
        emoji = "✅" if status == "granted" else "❌"
        print(f"{emoji} {permission}: {status}")

    print("\n" + "=" * 50)
    print("Required permissions for Instagram Reels:")
    print("=" * 50)

    required_perms = [
        'instagram_basic',
        'instagram_content_publish',
        'pages_read_engagement',
        'pages_show_list',
        'business_management'
    ]

    granted_perms = [p['permission'] for p in data.get('data', []) if p.get('status') == 'granted']

    for req_perm in required_perms:
        if req_perm in granted_perms:
            print(f"✅ {req_perm}")
        else:
            print(f"❌ {req_perm} - MISSING!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
