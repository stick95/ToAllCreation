# Twitter (X) Integration Documentation

## Overview

This document describes the Twitter (X) integration for the ToAllCreation social media posting platform. The integration allows users to connect their Twitter accounts and post videos as tweets.

## Architecture

The Twitter integration follows the same patterns as Facebook and Instagram integrations:

1. **OAuth 2.0 Authentication**: Users authenticate via Twitter OAuth 2.0 with PKCE
2. **Token Storage**: Access and refresh tokens stored in DynamoDB
3. **Async Posting**: Videos posted via SQS queue and Lambda worker
4. **API Endpoints**: RESTful API for account management and posting

## Components

### 1. OAuth Provider (`oauth_providers.py`)

**TwitterProvider** class handles OAuth 2.0 authorization URL generation.

**Key Features**:
- OAuth 2.0 with PKCE (Proof Key for Code Exchange)
- Required scopes: `tweet.read`, `tweet.write`, `users.read`, `offline.access`
- Authorization URL: `https://twitter.com/i/oauth2/authorize`

**Note**: Twitter OAuth 2.0 requires PKCE. Currently using simplified implementation with `code_challenge="challenge"` and `code_challenge_method="plain"`.

### 2. Token Exchange (`oauth_token_exchange.py`)

**TwitterTokenExchange** class handles exchanging authorization codes for access tokens.

**Key Features**:
- Exchanges authorization code for access + refresh tokens
- Uses Basic Auth (client_id, client_secret)
- Token URL: `https://api.twitter.com/2/oauth2/token`
- Access tokens expire in 2 hours
- Refresh tokens provided for long-term access

### 3. Posting Service (`twitter_posting.py`)

**TwitterPostingService** handles posting tweets with videos.

**Process Flow**:
1. Download video from S3
2. Upload video using chunked upload (v1.1 API)
   - INIT: Initialize upload session
   - APPEND: Upload video in 5MB chunks
   - FINALIZE: Complete upload and get media_id
3. Wait for video processing (if needed)
4. Create tweet with media_id (v2 API)

**API Endpoints Used**:
- Media Upload: `POST https://upload.twitter.com/1.1/media/upload.json`
- Tweet Creation: `POST https://api.twitter.com/2/tweets`
- User Info: `GET https://api.twitter.com/2/users/me`

**Video Limits**:
- Max size: 512 MB
- Chunk size: 5 MB
- Media category: `tweet_video`

### 4. Worker Integration (`posting_worker.py`)

**process_twitter_post()** function handles async posting.

**Process**:
1. Fetch account details from DynamoDB
2. Get access token and user ID
3. Call TwitterPostingService.post_video()
4. Update request status in DynamoDB

### 5. API Routes (`main.py`)

**OAuth Callback Handler** (`/api/social/callback`):
1. Exchange authorization code for tokens
2. Fetch user profile info
3. Create account in DynamoDB
4. Redirect to accounts page with success

**Key Difference from Facebook/Instagram**:
Twitter accounts are saved immediately (no page selection needed).

## Database Schema

### DynamoDB - social-accounts table

```
{
  "user_id": "cognito-user-id",
  "account_id": "twitter:twitter_user_id",
  "platform": "twitter",
  "platform_user_id": "twitter_user_id",
  "account_type": "user",
  "username": "@username",
  "access_token": "encrypted-token",
  "refresh_token": "encrypted-token",
  "token_expires_at": 1234567890,
  "profile_data": {
    "name": "Display Name",
    "username": "username"
  },
  "is_active": true,
  "created_at": 1234567890,
  "updated_at": 1234567890
}
```

## Configuration

### Environment Variables

Both Lambda functions require:
```yaml
TWITTER_CLIENT_ID: '{{resolve:ssm:/toallcreation/twitter/client_id}}'
TWITTER_CLIENT_SECRET: '{{resolve:ssm:/toallcreation/twitter/client_secret}}'
```

### SSM Parameters

Create these in AWS Systems Manager Parameter Store:

```bash
# Client ID (Standard String)
aws ssm put-parameter \
  --name "/toallcreation/twitter/client_id" \
  --value "YOUR_CLIENT_ID" \
  --type "String" \
  --region us-west-2

# Client Secret (Secure String for encryption)
aws ssm put-parameter \
  --name "/toallcreation/twitter/client_secret" \
  --value "YOUR_CLIENT_SECRET" \
  --type "SecureString" \
  --region us-west-2
```

## Twitter Developer Setup

### 1. Create Twitter App

1. Go to https://developer.x.com/
2. Create a new Project and App
3. Note your Client ID and Client Secret

### 2. Configure OAuth 2.0 Settings

**App Permissions**:
- Read and Write permissions required
- Enable "Request email from users" (optional)

**OAuth 2.0 Settings**:
- Type: Web App
- Callback URL: `https://YOUR_API_URL/api/social/callback`
- Website URL: `https://YOUR_FRONTEND_URL`

### 3. Required API Access

**Free Tier** (Recommended):
- ✅ Can post up to 1,500 tweets per month
- ✅ Can upload media (images and videos)
- ✅ Can authenticate users
- ✅ All required endpoints available (v1.1 media upload + v2 tweet creation)
- ⚠️ Limited read/data retrieval capabilities

**Basic Tier** ($200/month):
- ✅ Can post up to 3,000 tweets per month
- ✅ Can upload media
- ✅ Enhanced read capabilities

**Note**: The **Free tier is sufficient** for ToAllCreation's posting functionality! Our implementation uses the exact API combination (v1.1 for media + v2 for tweets) that works with the free tier.

### 4. Get OAuth Credentials

From your Twitter App settings:
- Copy "Client ID"
- Copy "Client Secret"
- Update SSM parameters with real values

## Testing

### 1. Test OAuth Flow

```bash
# 1. Initiate OAuth
curl https://YOUR_API_URL/api/social/connect/twitter \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Response includes authorization_url
# 2. Visit URL in browser, authorize app
# 3. User redirected to callback
# 4. Account saved to DynamoDB
```

### 2. Test Video Posting

```bash
# 1. Upload video to S3 (get presigned URL)
curl -X POST https://YOUR_API_URL/api/social/upload-url \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "video.mp4", "content_type": "video/mp4"}'

# 2. Upload video to S3 using presigned URL
# 3. Post to Twitter
curl -X POST https://YOUR_API_URL/api/social/post \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "uploads/USER_ID/VIDEO_ID.mp4",
    "caption": "Check out this video!",
    "account_ids": ["twitter:TWITTER_USER_ID"]
  }'

# Response includes request_id for tracking
# 4. Check status
curl https://YOUR_API_URL/api/social/uploads/REQUEST_ID \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Check Logs

```bash
# Worker Lambda logs
aws logs tail /aws/lambda/toallcreation-backend-PostingWorkerFunction-XXX \
  --follow \
  --region us-west-2
```

## Error Handling

### Common Errors

**1. Authentication Errors**
```
Error: "Twitter OAuth credentials not configured"
Solution: Check SSM parameters are set correctly
```

**2. Token Exchange Errors**
```
Error: "invalid_client"
Solution: Verify client_id and client_secret match Twitter App
```

**3. Upload Errors**
```
Error: "Upload initialization failed"
Solution: Check access token has media.write scope
```

**4. Video Processing Timeout**
```
Error: "Video processing timeout after 300s"
Solution: Video may be too large or corrupted
```

### Rate Limits

Twitter API v2 rate limits (per user):
- Tweet creation: 200 tweets per 15 min
- Media upload: 1 upload per 15 min (Free), more on paid tiers
- User lookup: 900 requests per 15 min

## Frontend Integration

### Account Connection UI

Twitter should appear in the accounts page alongside Facebook and Instagram:

```tsx
const platforms = [
  { id: 'facebook', name: 'Facebook', icon: FacebookIcon },
  { id: 'instagram', name: 'Instagram', icon: InstagramIcon },
  { id: 'twitter', name: 'Twitter (X)', icon: TwitterIcon }  // ADD THIS
]
```

### Account Display

Twitter accounts display format:
```
@username (Display Name)
```

### Posting UI

Tweet text limited to 280 characters. UI should show character count.

## Deployment

### 1. Build

```bash
cd backend
sam build
```

### 2. Validate

```bash
sam validate
```

### 3. Deploy

```bash
sam deploy --no-confirm-changeset
```

### 4. Verify

```bash
# Check environment variables are set
aws lambda get-function-configuration \
  --function-name toallcreation-backend-ApiFunction-XXX \
  --region us-west-2 \
  --query 'Environment.Variables'
```

## API Differences: Twitter vs Facebook/Instagram

| Feature | Facebook/Instagram | Twitter |
|---------|-------------------|---------|
| **OAuth Type** | OAuth 2.0 | OAuth 2.0 with PKCE |
| **Token Lifetime** | 60 days | 2 hours (with refresh) |
| **Account Selection** | Page selection UI | Direct save |
| **Media Upload** | v18.0 Graph API | v1.1 Upload API |
| **Post Creation** | Graph API | v2 Tweets API |
| **Text Limit** | No limit (caption) | 280 characters |
| **Video Processing** | Synchronous | May be async |
| **Free Tier** | Posting allowed | 1,500 posts/month |

## Next Steps

1. **Get Twitter API Access**: Apply for Free tier (sufficient for posting functionality!)
2. **Update SSM Parameters**: Replace placeholder values with real credentials
3. **Frontend Updates**: Add Twitter icon and account display
4. **Testing**: Test full OAuth and posting flow
5. **Token Refresh**: Implement automatic token refresh logic
6. **Monitoring**: Add CloudWatch alarms for Twitter API errors

## Resources

- [Twitter API v2 Documentation](https://developer.x.com/en/docs/twitter-api)
- [OAuth 2.0 Guide](https://developer.x.com/en/docs/authentication/oauth-2-0)
- [Media Upload Guide](https://developer.x.com/en/docs/twitter-api/v1/media/upload-media/overview)
- [Tweet Creation API](https://developer.x.com/en/docs/twitter-api/tweets/manage-tweets/introduction)

---

**Last Updated**: 2025-11-21
**Status**: Implementation Complete - Awaiting Testing
**Author**: Claude (via ToAllCreation development session)
