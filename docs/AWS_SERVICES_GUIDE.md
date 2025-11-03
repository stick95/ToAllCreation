# AWS Services Guide - ToAllCreation

Complete reference for all AWS services used in the ToAllCreation platform, including free tier limits, pricing, and best practices.

---

## Service Overview

| Service | Purpose | Free Tier | After Free Tier |
|---------|---------|-----------|-----------------|
| Lambda | API & background workers | 1M req/mo (permanent) | $0.20 per 1M requests |
| API Gateway | HTTP API endpoints | 1M req/mo (12 months) | $1.00 per 1M requests |
| DynamoDB | Database | 25 GB, 25 RCU/WCU (permanent) | Pay per request |
| S3 | File storage | 5 GB (12 months) | $0.023 per GB |
| CloudFront | CDN | 1 TB transfer (permanent) | $0.085 per GB |
| Cognito | Authentication | 50K MAU (permanent) | Tiered pricing |
| SQS | Message queue | 1M req/mo (permanent) | $0.40 per 1M requests |
| EventBridge | Scheduled tasks | AWS events free (permanent) | $1.00 per 1M custom events |
| Secrets Manager | Secret storage | $200 credit (6-12 mo) | $0.40 per secret/month |
| CloudWatch | Logging & monitoring | 5 GB logs (permanent) | $0.50 per GB |
| ACM | SSL certificates | Free (permanent) | Free |
| Route 53 | DNS (optional) | N/A | $0.50 per hosted zone/month |

---

## 1. AWS Lambda

### Overview
Serverless compute service that runs code in response to events without managing servers.

### ToAllCreation Usage
- **API Handler:** Main FastAPI application
- **Post Processor:** Async worker for publishing posts
- **Comment Sync:** Scheduled comment polling
- **Media Optimizer:** Video/image processing (optional)

### Configuration

**Runtime:** Python 3.12
**Architecture:** ARM64 (Graviton2 - 20% cheaper, 20% faster)
**Memory:** 512 MB (API), 256-1024 MB (workers)
**Timeout:** 30s (API), 5min (workers)

### Free Tier (Permanent)

- **Requests:** 1,000,000 per month
- **Compute:** 400,000 GB-seconds per month
- **Duration:** Permanent (doesn't expire)

**Example Calculation:**
- 512 MB function running for 200ms
- GB-seconds per request: 0.5 GB × 0.2s = 0.1 GB-seconds
- Free tier allows: 400,000 / 0.1 = 4 million requests

### Pricing After Free Tier

- **Requests:** $0.20 per 1 million requests
- **Duration:** $0.0000166667 per GB-second

**Example Monthly Cost (MVP):**
- 10,000 API requests × 200ms @ 512MB = 1,000 GB-seconds
- 100,000 background jobs × 500ms @ 512MB = 25,000 GB-seconds
- **Total:** Well within free tier ($0)

### Best Practices

1. **Use ARM64 Architecture**
   ```yaml
   Function:
     Properties:
       Architecture: arm64
   ```

2. **Right-Size Memory**
   - Start with 512 MB
   - Monitor performance
   - Adjust based on execution time

3. **Minimize Package Size**
   - Use Lambda Layers for shared dependencies
   - Remove unnecessary files
   - Use .gitignore patterns in SAM build

4. **Enable SnapStart (Python 3.12)**
   ```yaml
   Function:
     Properties:
       SnapStart:
         ApplyOn: PublishedVersions
   ```

5. **Environment Variables**
   ```yaml
   Environment:
     Variables:
       TABLE_NAME: !Ref ToAllCreationTable
       MEDIA_BUCKET: !Ref MediaBucket
   ```

### Monitoring

**CloudWatch Metrics:**
- Invocations
- Duration
- Errors
- Throttles
- Cold start rate

**Recommended Alarms:**
- Error rate > 1%
- Duration > 5 seconds
- Throttles > 0

---

## 2. Amazon API Gateway (HTTP API)

### Overview
Managed service for creating, deploying, and managing APIs.

### ToAllCreation Usage
REST API for frontend to access Lambda functions.

### Configuration

**Type:** HTTP API (not REST API - 70% cheaper)
**Protocol:** HTTPS only
**Authorization:** JWT from Cognito
**CORS:** Enabled for frontend domain

### Free Tier (12 Months)

- **Requests:** 1,000,000 per month
- **Duration:** First 12 months only

### Pricing After Free Tier

- **HTTP API:** $1.00 per million requests
- **WebSocket API:** $1.00 per million messages

**Example Monthly Cost:**
- 10,000 requests = $0.01
- 100,000 requests = $0.10
- 1,000,000 requests = $1.00

### Best Practices

1. **Use HTTP API Instead of REST API**
   - 70% cheaper
   - Faster
   - Simpler JWT validation

2. **Enable Caching (Optional)**
   ```yaml
   HttpApi:
     Properties:
       DefaultRouteSettings:
         ThrottlingBurstLimit: 5000
         ThrottlingRateLimit: 10000
   ```

3. **Configure CORS Properly**
   ```yaml
   CorsConfiguration:
     AllowOrigins:
       - https://app.toallcreation.com
     AllowMethods: [GET, POST, PUT, DELETE, OPTIONS]
     AllowHeaders: [Authorization, Content-Type]
     MaxAge: 3600
   ```

4. **Use Custom Domain (Optional)**
   ```yaml
   DomainName:
     Type: AWS::ApiGatewayV2::DomainName
     Properties:
       DomainName: api.toallcreation.com
       DomainNameConfigurations:
         - CertificateArn: !Ref Certificate
   ```

### Monitoring

**CloudWatch Metrics:**
- Count (total requests)
- Latency
- 4XXError
- 5XXError

**Recommended Alarms:**
- 5XXError rate > 1%
- Latency > 1000ms

---

## 3. Amazon DynamoDB

### Overview
NoSQL database service with single-digit millisecond performance at any scale.

### ToAllCreation Usage
Single-table design storing:
- User profiles
- Platform credentials
- Posts
- Comments
- Settings

### Configuration

**Table Name:** ToAllCreation
**Capacity Mode:** On-Demand (pay per request)
**Encryption:** AWS managed keys
**Streams:** Enabled for comment notifications

### Free Tier (Permanent)

- **Storage:** 25 GB
- **Read Capacity:** 25 RCU
- **Write Capacity:** 25 WCU
- **Data Transfer:** 25 GB
- **Streams:** 2.5 million stream read requests
- **Duration:** Permanent

### Pricing After Free Tier

**On-Demand Mode:**
- **Write:** $1.25 per million requests
- **Read:** $0.25 per million requests
- **Storage:** $0.25 per GB per month

**Provisioned Mode:**
- **Write:** $0.00065 per WCU per hour
- **Read:** $0.00013 per RCU per hour

**Example Monthly Cost (On-Demand):**
- Storage: 1 GB = $0.25
- Writes: 10,000 = $0.0125
- Reads: 50,000 = $0.0125
- **Total:** $0.275/month

### Best Practices

1. **Single-Table Design**
   ```
   PK: USER#123, SK: PROFILE
   PK: USER#123, SK: PLATFORM#FACEBOOK
   PK: POST#abc, SK: METADATA
   PK: POST#abc, SK: COMMENT#xyz
   ```

2. **Use On-Demand Capacity**
   - Unpredictable traffic
   - No capacity planning
   - Automatic scaling

3. **Add GSI for Reverse Lookups**
   ```yaml
   GlobalSecondaryIndexes:
     - IndexName: GSI1
       KeySchema:
         - AttributeName: GSI1PK
           KeyType: HASH
         - AttributeName: GSI1SK
           KeyType: RANGE
   ```

4. **Enable Streams for Real-Time Processing**
   ```yaml
   StreamSpecification:
     StreamViewType: NEW_AND_OLD_IMAGES
   ```

5. **Use TTL for Automatic Cleanup**
   ```yaml
   TimeToLiveSpecification:
     Enabled: true
     AttributeName: ttl
   ```

### Access Patterns

```python
# Get user profile
response = table.get_item(
    Key={'PK': 'USER#123', 'SK': 'PROFILE'}
)

# Get all user platforms
response = table.query(
    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues={
        ':pk': 'USER#123',
        ':sk': 'PLATFORM#'
    }
)

# Get post with all comments
response = table.query(
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={':pk': 'POST#abc'}
)
```

---

## 4. Amazon S3

### Overview
Object storage service with 99.999999999% durability.

### ToAllCreation Usage

**Buckets:**
1. **toallcreation-frontend-{account-id}:** React app hosting
2. **toallcreation-media-{account-id}:** Videos, images, thumbnails

### Configuration

**Storage Class:** Standard (hot data)
**Encryption:** SSE-S3 (AES-256)
**Versioning:** Enabled (frontend bucket only)
**Lifecycle:** Delete after 90 days (media bucket)

### Free Tier (12 Months)

- **Storage:** 5 GB Standard storage
- **Requests:** 20,000 GET, 2,000 PUT
- **Data Transfer:** 100 GB out per month
- **Duration:** First 12 months

### Pricing After Free Tier

**Storage:**
- **S3 Standard:** $0.023 per GB per month
- **S3 Intelligent-Tiering:** $0.023 per GB + monitoring fee
- **S3 Glacier:** $0.004 per GB per month

**Requests:**
- **PUT/POST:** $0.005 per 1,000 requests
- **GET:** $0.0004 per 1,000 requests

**Data Transfer:**
- **To CloudFront:** FREE
- **To Internet:** $0.09 per GB (after 100 GB)

**Example Monthly Cost:**
- Storage: 3 GB = $0.069
- GET: 5,000 requests = $0.002
- PUT: 500 requests = $0.0025
- **Total:** $0.07/month

### Best Practices

1. **CORS Configuration for Direct Uploads**
   ```json
   {
     "CORSRules": [
       {
         "AllowedOrigins": ["https://app.toallcreation.com"],
         "AllowedMethods": ["GET", "PUT", "POST"],
         "AllowedHeaders": ["*"],
         "MaxAgeSeconds": 3600
       }
     ]
   }
   ```

2. **Lifecycle Policies**
   ```yaml
   LifecycleConfiguration:
     Rules:
       - Id: DeleteOldVideos
         Status: Enabled
         ExpirationInDays: 90
       - Id: TransitionToIA
         Status: Enabled
         Transitions:
           - StorageClass: STANDARD_IA
             TransitionInDays: 30
   ```

3. **Pre-Signed URLs for Secure Uploads**
   ```python
   s3_client = boto3.client('s3')
   url = s3_client.generate_presigned_url(
       'put_object',
       Params={
           'Bucket': 'toallcreation-media',
           'Key': f'uploads/{filename}',
           'ContentType': 'video/mp4'
       },
       ExpiresIn=3600
   )
   ```

4. **Block Public Access (Except via CloudFront)**
   ```yaml
   PublicAccessBlockConfiguration:
     BlockPublicAcls: true
     BlockPublicPolicy: true
     IgnorePublicAcls: true
     RestrictPublicBuckets: true
   ```

---

## 5. Amazon CloudFront

### Overview
Content Delivery Network (CDN) with global edge locations.

### ToAllCreation Usage

**Distributions:**
1. **Frontend:** React SPA (S3 origin)
2. **Media:** Videos/images (S3 origin)

### Configuration

**Price Class:** Use North America and Europe (cheaper)
**Viewer Protocol:** HTTPS only (redirect HTTP)
**Cache:** 1 hour (frontend), 1 year (media)
**Compression:** Enabled (gzip, brotli)

### Free Tier (Permanent)

- **Data Transfer:** 1 TB per month
- **Requests:** 10 million HTTP/HTTPS per month
- **Duration:** Permanent

### Pricing After Free Tier

**Data Transfer Out:**
- **USA:** $0.085 per GB (after first TB)
- **Europe:** $0.085 per GB
- **Asia:** $0.14 per GB

**Requests:**
- **HTTP:** $0.0075 per 10,000 requests
- **HTTPS:** $0.01 per 10,000 requests

**Example Monthly Cost (within free tier):**
- Data Transfer: 50 GB = $0
- Requests: 500,000 = $0
- **Total:** $0/month

### Best Practices

1. **Optimize Cache-Control Headers**
   ```javascript
   // Frontend assets (immutable)
   Cache-Control: public, max-age=31536000, immutable

   // Media files
   Cache-Control: public, max-age=31536000

   // API responses (no cache)
   Cache-Control: no-store
   ```

2. **Use Origin Access Identity (OAI)**
   ```yaml
   OriginAccessIdentity:
     Type: AWS::CloudFront::CloudFrontOriginAccessIdentity
   ```

3. **Enable Compression**
   ```yaml
   DefaultCacheBehavior:
     Compress: true
   ```

4. **Custom Error Pages**
   ```yaml
   CustomErrorResponses:
     - ErrorCode: 404
       ResponseCode: 200
       ResponsePagePath: /index.html
   ```

5. **Invalidate Cache After Deployments**
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id E123456789 \
     --paths "/*"
   ```

---

## 6. AWS Cognito

### Overview
Managed authentication, authorization, and user management service.

### ToAllCreation Usage
User authentication with email/password and OAuth integration.

### Configuration

**Tier:** Essentials (default for new accounts)
**Sign-in:** Email + Password
**MFA:** TOTP (authenticator app, not SMS)
**Password Policy:** Strong (8+ chars, uppercase, number, symbol)

### Free Tier (Permanent)

- **Monthly Active Users (MAU):** 50,000
- **Duration:** Permanent

### Pricing After Free Tier

**Essentials Tier:**
- **First 50K MAU:** FREE
- **Next 50K (50K-100K):** $0.0055 per MAU
- **Next 100K (100K-200K):** $0.0046 per MAU

**Example:** Single user = $0/month

### Best Practices

1. **Strong Password Policy**
   ```yaml
   PasswordPolicy:
     MinimumLength: 8
     RequireUppercase: true
     RequireLowercase: true
     RequireNumbers: true
     RequireSymbols: true
   ```

2. **Use TOTP MFA (Not SMS)**
   ```yaml
   MfaConfiguration: OPTIONAL
   EnabledMfas:
     - SOFTWARE_TOKEN_MFA
   ```

3. **Email Configuration**
   ```yaml
   EmailConfiguration:
     EmailSendingAccount: COGNITO_DEFAULT
     # Or use SES for higher volume:
     # EmailSendingAccount: DEVELOPER
     # SourceArn: arn:aws:ses:...
   ```

4. **Custom Attributes**
   ```yaml
   Schema:
     - Name: ministry_name
       AttributeDataType: String
       Mutable: true
   ```

---

## 7. Amazon SQS

### Overview
Fully managed message queuing service.

### ToAllCreation Usage
Queue for async post publishing to platforms.

### Configuration

**Type:** Standard (high throughput, at-least-once delivery)
**Visibility Timeout:** 300 seconds (5 min)
**Retention:** 345,600 seconds (4 days)
**DLQ:** Enabled (max 3 retries)

### Free Tier (Permanent)

- **Requests:** 1,000,000 per month
- **Duration:** Permanent

### Pricing After Free Tier

- **Standard Queue:** $0.40 per million requests
- **FIFO Queue:** $0.50 per million requests
- **Data Transfer:** FREE (within AWS region)

**Example Monthly Cost:**
- 100,000 requests = $0.04/month

### Best Practices

1. **Dead Letter Queue**
   ```yaml
   RedrivePolicy:
     deadLetterTargetArn: !GetAtt PostDLQ.Arn
     maxReceiveCount: 3
   ```

2. **Message Attributes**
   ```python
   sqs.send_message(
       QueueUrl=queue_url,
       MessageBody=json.dumps(message),
       MessageAttributes={
           'Platform': {'StringValue': 'facebook', 'DataType': 'String'},
           'Priority': {'StringValue': 'high', 'DataType': 'String'}
       }
   )
   ```

3. **Batch Operations**
   ```python
   # Send up to 10 messages at once
   sqs.send_message_batch(
       QueueUrl=queue_url,
       Entries=[...]
   )
   ```

---

## 8. Amazon EventBridge

### Overview
Serverless event bus for building event-driven applications.

### ToAllCreation Usage
Scheduled tasks (cron jobs) for comment polling.

### Configuration

**Rules:**
- Comment sync: Every 15 minutes
- Cleanup: Daily at 2 AM

### Free Tier (Permanent)

- **AWS Events:** Unlimited (FREE)
- **Custom Events:** 1 million per month
- **Duration:** Permanent

### Pricing After Free Tier

- **Custom Events:** $1.00 per million events
- **AWS Events:** Always FREE

**Example Monthly Cost:**
- 3,000 scheduled events = $0/month (AWS events)

### Best Practices

1. **Schedule Expressions**
   ```yaml
   # Every 15 minutes
   ScheduleExpression: rate(15 minutes)

   # Daily at 2 AM UTC
   ScheduleExpression: cron(0 2 * * ? *)
   ```

2. **Target Lambda Functions**
   ```yaml
   Targets:
     - Arn: !GetAtt CommentSyncFunction.Arn
       Id: CommentSyncTarget
   ```

3. **Error Handling**
   ```yaml
   DeadLetterConfig:
     Arn: !GetAtt EventDLQ.Arn
   RetryPolicy:
     MaximumRetryAttempts: 2
   ```

---

## Total Cost Summary

### First 12 Months

| Service | Free Tier Usage | Cost |
|---------|-----------------|------|
| Lambda | 10K requests | $0 |
| API Gateway | 10K requests | $0 |
| DynamoDB | 1 GB, 5 WCU/RCU | $0 |
| S3 | 3 GB storage | $0 |
| CloudFront | 50 GB transfer | $0 |
| Cognito | 1 user | $0 |
| SQS | 100K requests | $0 |
| EventBridge | 3K events | $0 |
| Secrets Manager | 5 secrets | **$2.00** |
| Route 53 (optional) | 1 hosted zone | **$0.50** |
| **TOTAL** | | **~$2.50/month** |

### After 12 Months (Permanent Free Tier)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 10K requests | $0 |
| API Gateway | 10K requests | **$0.01** |
| DynamoDB | 1 GB, 5 WCU/RCU | $0 |
| S3 | 3 GB storage | **$0.07** |
| CloudFront | 50 GB transfer | $0 |
| Cognito | 1 user | $0 |
| SQS | 100K requests | $0 |
| EventBridge | 3K events | $0 |
| Secrets Manager | 5 secrets | **$2.00** |
| Route 53 (optional) | 1 hosted zone | **$0.50** |
| **TOTAL** | | **~$2.58/month** |

### Annual Cost

- **Year 1:** ~$30
- **Year 2+:** ~$31

---

## Cost Optimization Tips

1. **Replace Secrets Manager with SSM Parameter Store**
   - Savings: $2/month → $0/month
   - Trade-off: Manual token rotation

2. **Aggressive Video Compression**
   - Keep S3 under 5 GB free tier
   - Client-side or Lambda compression

3. **CloudFront Cache Optimization**
   - Maximize cache hit ratio
   - Reduce S3 requests and data transfer

4. **Lambda Optimization**
   - ARM64 architecture (20% cheaper)
   - Right-size memory allocation
   - Use Lambda Layers

5. **Monitor Usage with AWS Budgets**
   - Set budget: $5/month
   - Alert at 80% and 100%

---

**Complete AWS services guide for ToAllCreation platform**
