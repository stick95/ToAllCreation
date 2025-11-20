#!/usr/bin/env python3
"""
Check Instagram Business Account Connection
"""
import requests
import json

# Your page access token from the database
PAGE_ACCESS_TOKEN = "EAAv9uApP1u0BP4BWm9PO7QYera5L0T8zH3Ktb5CZBgrSZAQuxfMbK53bPkaWkEZALQfoBRfDP8MgRrrSdM79EcU8oZBSuc0CDeK9nOxJBlTRc89XaDQQz8WNA0T8vYc7cA0lcr9n5AN2IEnZA3rVvTgTWHQPJJoAjmIUIG1xfZA8RrkQYjKfyEZAxpUQvj8ElXHMgZDZD"
PAGE_ID = "872023199325243"

def get_instagram_account():
    """Get Instagram Business Account connected to the Page"""

    url = f"https://graph.facebook.com/v18.0/{PAGE_ID}"
    params = {
        'access_token': PAGE_ACCESS_TOKEN,
        'fields': 'instagram_business_account'
    }

    print("Checking for connected Instagram account...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print("\n=== PAGE INSTAGRAM CONNECTION ===")
        print(json.dumps(data, indent=2))

        ig_account_id = data.get('instagram_business_account', {}).get('id')

        if ig_account_id:
            print(f"\n✅ Instagram Business Account ID: {ig_account_id}")
            return ig_account_id
        else:
            print("\n❌ No Instagram account connected to this Page")
            return None
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_instagram_account_details(ig_account_id):
    """Get details about the Instagram account"""

    url = f"https://graph.facebook.com/v18.0/{ig_account_id}"
    params = {
        'access_token': PAGE_ACCESS_TOKEN,
        'fields': 'id,username,name,profile_picture_url,followers_count,follows_count,media_count'
    }

    print("\n\nFetching Instagram account details...")
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print("\n=== INSTAGRAM ACCOUNT DETAILS ===")
        print(json.dumps(data, indent=2))

        print("\n=== SUMMARY ===")
        print(f"Instagram ID: {data.get('id')}")
        print(f"Username: @{data.get('username')}")
        print(f"Name: {data.get('name')}")
        print(f"Followers: {data.get('followers_count')}")
        print(f"Following: {data.get('follows_count')}")
        print(f"Posts: {data.get('media_count')}")

        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    ig_account_id = get_instagram_account()

    if ig_account_id:
        get_instagram_account_details(ig_account_id)
        print("\n✅ Instagram is properly connected and ready for posting!")
    else:
        print("\n❌ Please connect your Instagram Business account to the Facebook Page")
