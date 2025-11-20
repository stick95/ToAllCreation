# Social Media Posting Architecture

## Overview

ToAllCreation posts to **Pages and Business accounts** that users manage, not personal profiles (except for Twitter/X).

## Platform-Specific Posting

### Facebook (📘)
- **Target**: Facebook Pages user manages
- **Not**: Personal profile
- **OAuth Flow**:
  1. User authorizes with Facebook
  2. Backend fetches list of Pages user can manage (with `CREATE_CONTENT` permission)
  3. User selects which Pages to connect
  4. Each Page gets its own access token stored in DynamoDB
- **Posting**: Uses Page-specific access token to post to Page timeline

### Instagram (📷)
- **Target**: Instagram Business accounts linked to Facebook Pages
- **Not**: Personal Instagram accounts
- **Requirements**: Must be Instagram Business account connected to a Facebook Page
- **OAuth Flow**:
  1. User authorizes Facebook (Instagram uses same OAuth)
  2. Backend fetches Facebook Pages
  3. For each Page, check if Instagram Business account is linked
  4. Store Instagram account credentials
- **Posting**: Uses Page access token to publish to Instagram Business account

### X / Twitter (🐦)
- **Target**: User's personal Twitter account
- **OAuth Flow**:
  1. User authorizes Twitter OAuth 2.0
  2. Store user's access token
- **Posting**: Posts to user's timeline

### LinkedIn (💼)
- **Target**: Personal profile OR Company Pages user manages
- **OAuth Flow**:
  1. User authorizes LinkedIn
  2. Backend fetches:
     - Personal profile (always available)
     - Organizations (Company Pages) where user has admin/editor role
  3. User selects which accounts to connect
- **Posting**: Can post to personal profile or organization pages

## Database Schema

### Social Accounts Table (`toallcreation-social-accounts`)

```
{
  user_id: string (HASH KEY)
  account_id: string (RANGE KEY) - format: "platform:id"
  platform: "facebook" | "instagram" | "twitter" | "linkedin"
  account_type: "personal" | "page" | "business"
  platform_user_id: string
  page_id: string (optional) - Facebook Page ID or LinkedIn Org ID
  page_name: string (optional) - Display name of page
  username: string (optional) - For Twitter/Instagram
  access_token: string (encrypted)
  refresh_token: string (optional)
  token_expires_at: number (unix timestamp)
  profile_data: object
  created_at: number
  updated_at: number
  is_active: boolean
}
```

## Required OAuth Scopes

### Facebook
```
pages_show_list              # List pages user manages
pages_manage_posts           # Post to Facebook pages
pages_read_engagement        # Read page data
instagram_basic              # Instagram access
instagram_content_publish    # Post to Instagram
business_management          # Access business assets
public_profile              # Basic profile info
```

### X (Twitter)
```
tweet.read
tweet.write
users.read
offline.access              # Refresh token
```

### LinkedIn
```
w_member_social             # Post to personal profile
w_organization_social       # Post to company pages
r_liteprofile              # Read profile
r_basicprofile             # Basic profile
r_organization_social       # Read organization info
```

## Multi-Platform Posting Flow

1. **User creates post** in ToAllCreation
2. **Selects target accounts** (e.g., 2 Facebook Pages, 1 Instagram, 1 Twitter)
3. **Backend processes**:
   - Validates user has access to each account
   - Retrieves platform-specific tokens from DynamoDB
   - Formats post for each platform's API
   - Posts to each platform in parallel
   - Tracks success/failure per platform
4. **User sees results** for each platform

## Page Selection UI Flow

### After OAuth Authorization:

1. User clicks "Connect Facebook"
2. Redirected to Facebook OAuth
3. User authorizes permissions
4. Redirected back to ToAllCreation
5. **Backend fetches available Pages**
6. **Frontend shows Page selection modal**:
   ```
   Select Facebook Pages to Connect:
   ☐ My Business Page (Category: Local Business)
   ☐ Non-Profit Organization (Category: Non-Profit)
   ☐ Community Page (Category: Community)

   [Connect Selected Pages]
   ```
7. User selects desired Pages
8. Each selected Page is stored as separate account in DynamoDB

## API Endpoints

```
GET  /api/social/accounts              # List connected accounts
GET  /api/social/connect/{platform}    # Initiate OAuth
GET  /api/social/callback              # OAuth callback
GET  /api/social/pages/{platform}      # Get available pages/accounts
POST /api/social/accounts/select       # Save selected pages
DELETE /api/social/accounts/{id}       # Disconnect account

POST /api/posts                        # Create multi-platform post
GET  /api/posts                        # List post history
GET  /api/posts/{id}                   # Get post details
```

## Implementation Status

✅ DynamoDB schema with page support
✅ OAuth providers with page permissions
✅ Service to fetch Facebook Pages
✅ Service to fetch Instagram Business accounts
✅ Service to fetch LinkedIn Organizations
✅ Account Management UI with descriptions
✅ API endpoint to list available pages

⏳ OAuth token exchange implementation
⏳ Page selection modal UI
⏳ Save selected pages to DynamoDB
⏳ Multi-platform posting API
⏳ Post composer UI

## Next Steps

1. Register apps on each platform:
   - Facebook: https://developers.facebook.com/apps
   - Twitter: https://developer.twitter.com/
   - LinkedIn: https://www.linkedin.com/developers/apps

2. Configure OAuth credentials in AWS:
   - Add env vars to SAM template
   - Deploy to Lambda

3. Implement token exchange in OAuth callback

4. Build page selection modal UI

5. Test end-to-end OAuth flow with real accounts
