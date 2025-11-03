# ToAllCreation - Comprehensive Architecture Design

**Version:** 1.0
**Date:** November 3, 2025
**Status:** Initial Architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture Overview](#system-architecture-overview)
3. [Social Media Platform Analysis](#social-media-platform-analysis)
4. [Technology Stack Recommendations](#technology-stack-recommendations)
5. [AWS Infrastructure Design](#aws-infrastructure-design)
6. [Backend Architecture](#backend-architecture)
7. [Frontend Architecture](#frontend-architecture)
8. [Security & Authentication](#security--authentication)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Cost Analysis & Free Tier Strategy](#cost-analysis--free-tier-strategy)
11. [Implementation Roadmap](#implementation-roadmap)
12. [Technical Decisions Requiring Input](#technical-decisions-requiring-input)
13. [Challenges & Mitigation Strategies](#challenges--mitigation-strategies)
14. [Alternative Architectural Approaches](#alternative-architectural-approaches)

---

## Executive Summary

ToAllCreation is a serverless social media aggregator designed to help spread the gospel through multi-platform posting. The architecture prioritizes:

- **Zero-cost operation** within AWS Free Tier
- **Serverless-first** approach for automatic scaling
- **Single-user MVP** with path to multi-user
- **Simple, maintainable** codebase
- **Gospel-focused mission** with donation capabilities

### Key Architectural Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend** | FastAPI + AWS Lambda | Modern async, automatic docs, fastest Python framework |
| **Frontend** | React + Vite + S3/CloudFront | Simple SPA, no SSR overhead, CDN distribution |
| **Database** | DynamoDB (Single-Table) | Serverless, permanent free tier, auto-scaling |
| **Authentication** | AWS Cognito Essentials | Managed auth, free tier, OAuth integration |
| **File Storage** | S3 + CloudFront | Video/image hosting, CDN delivery, free tier generous |
| **Job Queue** | SQS | Async posting, permanent free tier, simple |
| **Secrets** | AWS Secrets Manager | Secure token storage, rotation support |
| **CI/CD** | GitHub Actions | Native AWS integration, free for public repos |

---

## System Architecture Overview

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │           React SPA (Vite) - Hosted on S3                    │   │
│  │  • Post Composer  • Platform Manager  • Comment Dashboard    │   │
│  └────────────────┬─────────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────────┘
                    │ HTTPS
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CLOUDFRONT CDN                                  │
│        • Static Assets  • Global Distribution  • HTTPS              │
└───────────────────┬─────────────────────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────────────────────────┐
│  S3 BUCKET      │   │    API GATEWAY (HTTP API)           │
│  Static Files   │   │    • REST Endpoints                 │
└─────────────────┘   │    • CORS                           │
                      │    • JWT Validation                 │
                      └────────────┬────────────────────────┘
                                   │
                      ┌────────────┴────────────┐
                      │                         │
                      ▼                         ▼
            ┌──────────────────┐      ┌──────────────────┐
            │  AWS COGNITO     │      │  LAMBDA FUNCTIONS │
            │  • User Auth     │      │  (FastAPI + Mangum)│
            │  • JWT Tokens    │      │                   │
            │  • OAuth Flow    │      │  • API Handler    │
            └──────────────────┘      │  • Post Manager   │
                                      │  • Comment Sync   │
                                      │  • Media Processor│
                                      └─────────┬─────────┘
                                                │
                  ┌─────────────────────────────┼──────────────────┐
                  │                             │                  │
                  ▼                             ▼                  ▼
        ┌──────────────────┐         ┌──────────────────┐  ┌──────────────┐
        │   DYNAMODB       │         │      SQS         │  │  S3 BUCKET   │
        │  Single Table    │         │  • Post Queue    │  │  Media Files │
        │  • Users         │         │  • Retry Logic   │  │  • Videos    │
        │  • Posts         │         │                  │  │  • Images    │
        │  • Comments      │         └────────┬─────────┘  └──────────────┘
        │  • Platforms     │                  │
        └──────────────────┘                  │
                                              ▼
                                   ┌──────────────────────┐
                                   │ LAMBDA (SQS Consumer)│
                                   │  • Platform Posting  │
                                   │  • Error Handling    │
                                   └──────────┬───────────┘
                                              │
                  ┌───────────────────────────┼────────────────────┐
                  │                           │                    │
                  ▼                           ▼                    ▼
        ┌──────────────────┐      ┌──────────────────┐  ┌──────────────────┐
        │ SECRETS MANAGER  │      │  SOCIAL MEDIA    │  │    EVENTBRIDGE   │
        │  • API Keys      │      │    PLATFORMS     │  │  • Scheduled Jobs │
        │  • Tokens        │      │  • Facebook      │  │  • Comment Polling│
        │  • Credentials   │      │  • Instagram     │  └──────────────────┘
        └──────────────────┘      │  • YouTube       │
                                  │  • LinkedIn      │
                                  │  • TikTok (opt.) │
                                  │  • X/Twitter ($$)│
                                  └──────────────────┘
```

### Data Flow - Post Creation

```
1. User creates post in React UI
2. Upload media to S3 (if applicable)
3. POST to API Gateway → Lambda (FastAPI)
4. Lambda validates & stores post in DynamoDB
5. Lambda sends message to SQS queue (one per platform)
6. SQS Consumer Lambda triggered
7. Consumer retrieves credentials from Secrets Manager
8. Consumer posts to social media platform
9. Consumer updates post status in DynamoDB
10. WebSocket (future) or polling updates UI
```

### Data Flow - Comment Aggregation (Phase 2)

```
1. EventBridge triggers scheduled Lambda (every 5-15 min)
2. Lambda retrieves platform credentials
3. Lambda polls each platform for new comments
4. New comments stored in DynamoDB
5. DynamoDB Streams trigger notification Lambda
6. Frontend polls for new comments or receives push notification
```

---

## Social Media Platform Analysis

### Platform Comparison Matrix

| Platform | Posting API | Video Support | Reels/Shorts | Comments API | Webhooks | Authentication | Monthly Rate Limit | Cost | Difficulty |
|----------|-------------|---------------|--------------|--------------|----------|----------------|-------------------|------|------------|
| **Facebook** | ✅ Graph API | ✅ Yes | ✅ Reels | ✅ Yes | ✅ Yes | OAuth 2.0 | Varies by app | FREE | Medium |
| **Instagram** | ✅ Graph API | ✅ IGTV | ✅ Reels | ✅ Yes | ⚠️ Limited | OAuth 2.0, Requires Business Account | 25 posts/day | FREE | High |
| **YouTube** | ✅ Data API v3 | ✅ Yes | ✅ Shorts | ✅ Yes | ❌ No | OAuth 2.0 | 6-20 uploads/day | FREE | Medium |
| **LinkedIn** | ✅ Posts API | ✅ Yes | ❌ No | ✅ Yes | ❌ No | OAuth 2.0, Requires Approval | Varies | FREE | High |
| **TikTok** | ✅ Content API | ✅ Yes | ✅ Native | ⚠️ Limited | ❌ No | OAuth 2.0 | 30 posts/day | FREE | Medium |
| **X/Twitter** | ✅ API v2 | ✅ Yes | ❌ No | ✅ Yes | ❌ No | OAuth 2.0 | 1,500/month FREE, 50k/month at $100 | **PAID** | High |

### Platform-Specific Details

#### **Facebook**
- **Status:** RECOMMENDED for MVP
- **API:** Graph API v19.0+
- **Requirements:**
  - Facebook App registration
  - Page access token
  - `pages_manage_posts`, `pages_read_engagement` permissions
- **Rate Limits:** 200 calls/hour/user (generous)
- **Posting:** Direct posting to pages, supports images, videos, links
- **Comments:** Full read/write access via webhooks
- **Webhooks:** Real-time comment notifications
- **Cost:** FREE
- **Notes:** Most mature and reliable API

#### **Instagram**
- **Status:** RECOMMENDED for MVP (with caveats)
- **API:** Instagram Graph API
- **Requirements:**
  - Business or Creator account
  - Connected to Facebook Page
  - Facebook App with Instagram permissions
  - Business verification (for some features)
- **Rate Limits:** 25 posts per day (API publishing)
- **Posting:**
  - Images (JPEG only)
  - Videos (IGTV)
  - Reels (up to 90 seconds)
  - Single posts and carousels
- **Comments:** Read access via webhooks, limited write
- **Webhooks:** Comments, mentions, story mentions
- **Cost:** FREE
- **Notes:** Complex setup, requires business account linkage

#### **YouTube**
- **Status:** RECOMMENDED for MVP
- **API:** YouTube Data API v3
- **Requirements:**
  - Google Cloud Project
  - OAuth 2.0 consent screen
  - Channel ownership verification
- **Rate Limits:**
  - 10,000 quota units/day
  - Video upload = 1,600 units
  - ~6-20 uploads/day depending on other operations
- **Posting:** Video uploads, metadata, thumbnails, playlists
- **Comments:** Full read/write access
- **Webhooks:** Via PubSubHubbub (complex setup)
- **Cost:** FREE (within quota)
- **Notes:** Quota management is critical

#### **LinkedIn**
- **Status:** OPTIONAL for MVP
- **API:** LinkedIn Marketing API / Posts API
- **Requirements:**
  - LinkedIn App registration
  - Partner Program approval (for some features)
  - Company page (for organizational posts)
- **Rate Limits:** Varies by permission level
- **Posting:** Text, images, videos, articles
- **Comments:** Read access, limited write
- **Webhooks:** No native support
- **Cost:** FREE (with approved access)
- **Notes:** API access requires application/approval process

#### **TikTok**
- **Status:** OPTIONAL for Phase 2
- **API:** TikTok Content Posting API
- **Requirements:**
  - TikTok for Developers account
  - App registration and approval
  - OAuth 2.0 flow
- **Rate Limits:**
  - 6 requests/minute per user token
  - ~30 posts/day
- **Posting:** Video content only (native TikTok format)
- **Comments:** Limited read access
- **Webhooks:** No native support
- **Cost:** FREE
- **Notes:** Primarily video-focused, newer API with evolving features

#### **X/Twitter**
- **Status:** NOT RECOMMENDED for MVP (Cost)
- **API:** Twitter API v2
- **Requirements:**
  - Developer account
  - Elevated or paid access for posting
- **Rate Limits:**
  - **Free:** 1,500 tweets/month (recently reduced from 1,500 to 500)
  - **Basic:** $100-200/month for 50,000 tweets
  - **Pro:** $5,000/month
- **Posting:** Tweets, images, videos
- **Comments:** Read/write access (paid tiers)
- **Webhooks:** No (Enterprise only)
- **Cost:** **$100-200/month minimum** for meaningful use
- **Notes:** **MAJOR COST BARRIER** - Only consider if ministry specifically requires Twitter presence

### Recommended MVP Platform Support

**Phase 1 (MVP):**
1. ✅ Facebook (easiest, most reliable)
2. ✅ YouTube (essential for video content)
3. ✅ Instagram (important for reach, but complex)

**Phase 2:**
4. LinkedIn (professional audience)
5. TikTok (short-form video expansion)

**Explicitly Excluded from Free Tier:**
- ❌ X/Twitter (minimum $100/month, not feasible for free tier)

---

## Technology Stack Recommendations

### Backend Stack

#### **Python Framework: FastAPI**

**Selected:** ✅ FastAPI
**Alternatives Considered:** Flask, Django

**Justification:**
- **Performance:** Async/await support, one of fastest Python frameworks
- **Serverless Ready:** Works seamlessly with AWS Lambda via Mangum adapter
- **Automatic API Docs:** Built-in OpenAPI (Swagger) documentation
- **Modern Development:** Type hints, Pydantic validation, dependency injection
- **Small Cold Starts:** Minimal overhead compared to Django
- **2025 Trend:** Industry moving toward FastAPI for new serverless projects

**Setup:**
```python
# FastAPI + Mangum for Lambda
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "ToAllCreation API"}

# Lambda handler
handler = Mangum(app)
```

**Key Dependencies:**
- `fastapi` - Core framework
- `mangum` - ASGI adapter for AWS Lambda
- `pydantic` - Data validation
- `boto3` - AWS SDK
- `httpx` - Async HTTP client for social media APIs

#### **API Integration Strategy**

**Option 1: Direct Integration (RECOMMENDED for MVP)**
- Implement individual platform SDKs/REST clients
- Full control over rate limiting and error handling
- No additional costs
- More development time

**Option 2: Unified API Service (Consider for Phase 2)**
- Services like Ayrshare, Late, or Buffer
- Single API for multiple platforms
- Costs: ~$20-50/month minimum
- Faster development but adds dependency

**Recommendation:** Start with direct integration for cost control, evaluate unified services if scaling demands it.

---

### Frontend Stack

#### **Framework: React + Vite**

**Selected:** ✅ React + Vite
**Alternatives Considered:** Next.js, Create React App

**Justification:**
- **Vite Advantages:**
  - Ultra-fast development server
  - Lightning-fast hot module replacement
  - Optimized build output
  - Simple deployment to S3 (static files)
  - Framework agnostic (future flexibility)
  - Tiny bundle size (~1KB overhead)

- **Why NOT Next.js:**
  - SSR/SSG adds complexity for serverless deployment
  - Requires EC2, ECS, or Vercel (costs money)
  - Overkill for single-user SPA
  - SEO not critical for authenticated admin app

- **Why NOT Create React App:**
  - Slower build times
  - Webpack overhead
  - Being phased out by React team

**Setup:**
```bash
npm create vite@latest toallcreation-ui -- --template react-ts
```

#### **State Management: Zustand**

**Selected:** ✅ Zustand
**Alternatives Considered:** Redux Toolkit, React Context

**Justification:**
- **Simplicity:** Minimal boilerplate, ~1KB bundle
- **Performance:** Fast re-renders, no Provider overhead
- **Server-Friendly:** Works with SSR/SSG if needed later
- **2025 Standard:** Becoming default for medium-sized React apps
- **DevTools:** Supports Redux DevTools
- **Async Support:** Built-in middleware for async actions

**Example Store:**
```typescript
import { create } from 'zustand'

interface Post {
  id: string
  content: string
  platforms: string[]
  status: 'draft' | 'scheduled' | 'posted'
}

interface PostStore {
  posts: Post[]
  addPost: (post: Post) => void
  updatePost: (id: string, updates: Partial<Post>) => void
}

export const usePostStore = create<PostStore>((set) => ({
  posts: [],
  addPost: (post) => set((state) => ({ posts: [...state.posts, post] })),
  updatePost: (id, updates) => set((state) => ({
    posts: state.posts.map(p => p.id === id ? { ...p, ...updates } : p)
  }))
}))
```

#### **UI Component Library**

**Options:**

1. **Shadcn/ui (RECOMMENDED)**
   - Tailwind-based components
   - Copy-paste, fully customizable
   - No package dependencies
   - Modern, accessible
   - Free and open source

2. **Chakra UI**
   - Component-based
   - Accessible by default
   - Larger bundle size
   - Good TypeScript support

3. **Material-UI (MUI)**
   - Comprehensive component set
   - Heavy bundle size
   - Enterprise-grade
   - May be overkill for MVP

**Recommendation:** Shadcn/ui for customization and small bundle size

#### **Additional Frontend Tools**

- **React Router v6** - Client-side routing
- **React Query (TanStack Query)** - Server state management, caching
- **Axios or Fetch** - HTTP client
- **React Hook Form** - Form handling
- **date-fns** - Date manipulation (smaller than moment.js)
- **React Dropzone** - File uploads

---

### Database: DynamoDB

#### **Table Design: Single-Table Design**

**Selected:** ✅ Single-Table Design
**Alternative:** Multi-Table Design

**Justification:**
- **Free Tier Efficiency:** Consolidates 25 RCU/25 WCU into one table
- **Cost Savings:** No additional capacity for multiple tables
- **Performance:** Single query for related data
- **Scalability:** Easier to partition and scale
- **Best Practice:** AWS recommended pattern for serverless

#### **Single-Table Schema**

**Primary Key Pattern:**
- **PK (Partition Key):** Entity identifier
- **SK (Sort Key):** Entity type + metadata

**Entity Examples:**

```
┌─────────────────────┬──────────────────────────┬─────────────────────┐
│        PK           │           SK             │    Attributes       │
├─────────────────────┼──────────────────────────┼─────────────────────┤
│ USER#<userId>       │ PROFILE                  │ email, name, ...    │
│ USER#<userId>       │ PLATFORM#FACEBOOK        │ token, pageId, ...  │
│ USER#<userId>       │ PLATFORM#INSTAGRAM       │ token, accountId... │
│ USER#<userId>       │ POST#<timestamp>         │ content, status...  │
│ POST#<postId>       │ METADATA                 │ platforms, media... │
│ POST#<postId>       │ PLATFORM#FB#<platformId> │ fbPostId, status... │
│ POST#<postId>       │ COMMENT#<commentId>      │ text, platform...   │
└─────────────────────┴──────────────────────────┴─────────────────────┘
```

**Access Patterns:**
1. Get user profile: `PK = USER#<userId>, SK = PROFILE`
2. Get all user platforms: `PK = USER#<userId>, SK begins_with PLATFORM#`
3. Get all user posts: `PK = USER#<userId>, SK begins_with POST#`
4. Get post details: `PK = POST#<postId>, SK = METADATA`
5. Get post comments: `PK = POST#<postId>, SK begins_with COMMENT#`

**Global Secondary Index (GSI):**
- **GSI1PK:** For reverse lookups (e.g., find post by platform post ID)
- **GSI1SK:** Secondary sort key

**DynamoDB Free Tier:**
- 25 GB storage
- 25 WCU (Write Capacity Units)
- 25 RCU (Read Capacity Units)
- Permanent (doesn't expire after 12 months)

---

## AWS Infrastructure Design

### Serverless Components

#### **1. AWS Lambda**

**Functions:**

```
┌─────────────────────────────────────────────────────────────┐
│  Lambda Function        │  Trigger         │  Purpose       │
├─────────────────────────────────────────────────────────────┤
│  api-handler            │  API Gateway     │  Main API      │
│  post-processor         │  SQS             │  Post to       │
│                         │                  │  platforms     │
│  comment-sync           │  EventBridge     │  Poll comments │
│  media-optimizer        │  S3 Event        │  Process       │
│                         │                  │  uploads       │
└─────────────────────────────────────────────────────────────┘
```

**Configuration:**
- **Runtime:** Python 3.12 (latest)
- **Memory:** 512 MB (balance cost/performance)
- **Timeout:** 30s (API), 5min (async processors)
- **Architecture:** arm64 (Graviton2 - 20% cheaper, faster)
- **Environment:** Environment variables for config
- **Layers:** Shared dependencies (boto3, requests, etc.)

**Free Tier:**
- 1 million requests/month
- 400,000 GB-seconds compute time/month
- **Estimate:** Should cover 10,000+ API calls and 1,000+ posts/month easily

**Cold Start Mitigation:**
- Keep functions warm with scheduled ping (if needed)
- Use Lambda SnapStart (Python support as of 2024)
- Minimize package size
- Use Lambda Layers for shared dependencies

#### **2. API Gateway (HTTP API)**

**Selected:** HTTP API (not REST API)

**Why HTTP API over REST API:**
- **70% cheaper** than REST API
- **Faster** (lower latency)
- **Simpler** JWT validation
- **CORS** built-in
- **Sufficient** for MVP needs

**Configuration:**
- **Protocol:** HTTP API
- **CORS:** Enabled for frontend domain
- **Authorization:** JWT from Cognito
- **Throttling:** Use default limits (10,000 req/sec)
- **Custom Domain:** Optional (Route 53 + ACM certificate)

**Free Tier:**
- 1 million API calls/month (first 12 months)
- After: $1.00 per million requests

**Endpoints:**
```
POST   /api/auth/login
POST   /api/auth/callback
GET    /api/platforms
POST   /api/platforms/{platform}/connect
DELETE /api/platforms/{platform}/disconnect
GET    /api/posts
POST   /api/posts
GET    /api/posts/{postId}
PUT    /api/posts/{postId}
DELETE /api/posts/{postId}
POST   /api/posts/{postId}/publish
GET    /api/comments
POST   /api/comments/{commentId}/reply
GET    /api/media/upload-url
```

#### **3. Amazon S3**

**Buckets:**

1. **toallcreation-frontend** (Static Website Hosting)
   - Hosts React SPA
   - CloudFront origin
   - Public read access via CloudFront

2. **toallcreation-media** (Media Storage)
   - Videos, images, thumbnails
   - Private bucket
   - Pre-signed URLs for uploads
   - Lifecycle policies for cost optimization

**Configuration:**
- **Versioning:** Enabled (frontend bucket for rollback)
- **Encryption:** SSE-S3 (server-side encryption)
- **Lifecycle Rules:**
  - Move infrequent access media to S3-IA after 90 days
  - Delete failed uploads after 7 days
- **CORS:** Enabled for direct browser uploads

**Free Tier:**
- 5 GB storage
- 20,000 GET requests
- 2,000 PUT requests
- **Caution:** Video storage can exceed 5GB quickly

**Cost Mitigation:**
- Compress videos before upload
- Delete old/unused media
- Use S3 lifecycle policies
- Consider S3 Intelligent-Tiering

#### **4. CloudFront**

**Distributions:**
1. Frontend SPA (S3 origin)
2. Media files (S3 origin)

**Configuration:**
- **Price Class:** Use Only North America and Europe (cheaper)
- **Caching:**
  - Frontend: Cache for 1 hour, invalidate on deploy
  - Media: Cache for 1 year (immutable URLs)
- **Compression:** Enable automatic gzip/brotli
- **HTTPS:** Required (free AWS certificate via ACM)
- **Custom Domain:** Optional via Route 53

**Free Tier:**
- 1 TB data transfer out/month (permanent)
- 10 million HTTP/HTTPS requests/month
- **Excellent for video delivery**

#### **5. Amazon DynamoDB**

**Table:** `ToAllCreation` (single table)

**Configuration:**
- **Capacity Mode:** On-Demand (pay-per-request)
  - Why: Unpredictable traffic, free tier is in on-demand units
  - Provisioned mode requires 25 RCU/WCU which may waste capacity
- **Encryption:** AWS-managed keys
- **Streams:** Enabled for comment notifications
- **Point-in-Time Recovery:** Optional (costs extra, consider for production)

**Free Tier:**
- 25 GB storage
- 25 WCU and 25 RCU (if provisioned mode)
- 2.5M stream read requests (if streams enabled)

**Indexes:**
- GSI1: PlatformPostLookup (for reverse queries)

#### **6. Amazon SQS**

**Queues:**
- **post-queue.fifo** (FIFO for ordered processing per platform)
  - OR **post-queue** (Standard for higher throughput)

**Configuration:**
- **Type:** Standard (sufficient for MVP, higher throughput)
- **Visibility Timeout:** 5 minutes
- **Retention:** 4 days (default)
- **Dead Letter Queue:** post-dlq (for failed messages)
- **Max Receives:** 3 (retry 3 times before DLQ)

**Free Tier:**
- 1 million requests/month (permanent)
- Should cover 1,000+ posts/month easily

#### **7. AWS Cognito**

**User Pool:** ToAllCreation-Users

**Configuration:**
- **Tier:** Essentials (default for new accounts)
- **Sign-in:** Email + Password
- **MFA:** Optional (SMS costs extra, use TOTP/authenticator app)
- **Password Policy:** Strong (8+ chars, uppercase, number, symbol)
- **Email:**
  - Use Cognito email (50 emails/day free)
  - For production: SES (50,000 emails/month free)
- **Custom Domain:** Optional (Route 53)

**Free Tier:**
- 50,000 MAU (Monthly Active Users) - Essentials tier
- Single user MVP = well within free tier

**OAuth 2.0 Integration:**
- Cognito Hosted UI for social logins
- Custom redirect URLs
- Token management

#### **8. AWS Secrets Manager**

**Secrets Stored:**
- Social media platform API keys
- OAuth tokens and refresh tokens
- Database credentials (if using RDS)
- Third-party service keys

**Configuration:**
- **Rotation:** Automatic for supported secrets
- **Encryption:** AWS KMS (default key)

**Free Tier:**
- **NO permanent free tier** (as of July 2025)
- **New accounts:** $200 credit (first 6-12 months)
- **Cost:** $0.40/secret/month + $0.05/10,000 API calls

**Alternative: AWS Systems Manager Parameter Store**
- **Free Tier:** 10,000 parameters
- **Standard parameters:** Free
- **Advanced parameters:** $0.05/parameter/month
- **Limitation:** No automatic rotation
- **Recommendation:** Use Parameter Store for static keys, Secrets Manager for rotating credentials

**Cost Estimate:**
- 5 social platforms = 5 secrets = $2/month
- **Workaround for free tier:** Use encrypted SSM parameters instead

#### **9. Amazon EventBridge**

**Rules:**
- **comment-sync-schedule:** Every 15 minutes (96 invocations/day)
- **cleanup-old-posts:** Daily at 2 AM

**Configuration:**
- **Target:** Lambda functions
- **Error Handling:** DLQ for failed invocations

**Free Tier:**
- All events from AWS services are free
- Custom events: 1 million/month
- **Cost:** Essentially free for MVP

#### **10. AWS Certificate Manager (ACM)**

**Certificates:**
- Free SSL/TLS certificates for CloudFront and API Gateway
- Auto-renewal

**Free Tier:** Completely free

---

### Infrastructure as Code (IaC)

#### **Recommended Tool: AWS SAM (Serverless Application Model)**

**Alternatives Considered:**
- Serverless Framework
- Terraform
- AWS CDK
- CloudFormation (raw)

**Why SAM:**
- **AWS Native:** First-class Lambda support
- **Simple Syntax:** YAML-based, less verbose than CloudFormation
- **Local Testing:** `sam local` for testing Lambda functions
- **Free:** No additional costs
- **CI/CD:** Native GitHub Actions support
- **Transform:** Compiles to CloudFormation

**Example SAM Template:**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.12
    Timeout: 30
    MemorySize: 512
    Architecture: arm64
    Environment:
      Variables:
        TABLE_NAME: !Ref ToAllCreationTable

Resources:
  ToAllCreationAPI:
    Type: AWS::Serverless::HttpApi
    Properties:
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - POST
          - PUT
          - DELETE
        AllowHeaders:
          - "*"
      Auth:
        Authorizers:
          CognitoAuthorizer:
            IdentitySource: $request.header.Authorization
            JwtConfiguration:
              issuer: !Sub https://cognito-idp.${AWS::Region}.amazonaws.com/${UserPool}
              audience:
                - !Ref UserPoolClient

  ApiFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: backend/
      Handler: app.main.handler
      Events:
        ApiEvent:
          Type: HttpApi
          Properties:
            ApiId: !Ref ToAllCreationAPI
            Path: /{proxy+}
            Method: ANY

  ToAllCreationTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: ToAllCreation
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE

  UserPool:
    Type: AWS::Cognito::UserPool
    Properties:
      UserPoolName: ToAllCreationUsers
      AutoVerifiedAttributes:
        - email
      Schema:
        - Name: email
          Required: true
          Mutable: false

  UserPoolClient:
    Type: AWS::Cognito::UserPoolClient
    Properties:
      UserPoolId: !Ref UserPool
      ExplicitAuthFlows:
        - ALLOW_USER_PASSWORD_AUTH
        - ALLOW_REFRESH_TOKEN_AUTH
```

---

### Cost Breakdown (Monthly Estimates)

#### **AWS Free Tier Coverage (First 12 Months)**

| Service | Free Tier | MVP Usage | Cost |
|---------|-----------|-----------|------|
| Lambda | 1M requests, 400K GB-sec | 10K requests, 50K GB-sec | $0 |
| API Gateway | 1M requests | 10K requests | $0 |
| DynamoDB | 25 GB, 25 WCU/RCU | 1 GB, 5 WCU/RCU | $0 |
| S3 Storage | 5 GB | 3 GB (with video compression) | $0 |
| S3 Requests | 20K GET, 2K PUT | 5K GET, 500 PUT | $0 |
| CloudFront | 1 TB, 10M requests | 50 GB, 500K requests | $0 |
| SQS | 1M requests | 100K requests | $0 |
| Cognito | 50K MAU | 1 MAU | $0 |
| EventBridge | 1M custom events | 3K events | $0 |
| ACM | Free SSL | 2 certificates | $0 |
| **Secrets Manager** | **$200 credit** | **5 secrets** | **$2*** |

**Total Monthly Cost (First 12 Months):** ~$2/month (Secrets Manager only)

#### **AWS Free Tier Coverage (After 12 Months - Permanent Free Tier)**

| Service | Permanent Free Tier | Cost After |
|---------|---------------------|------------|
| Lambda | 1M requests, 400K GB-sec | $0 |
| API Gateway | None | ~$10/month (1M requests) |
| DynamoDB | 25 GB, 25 WCU/RCU | $0 |
| S3 Storage | None | ~$0.69/month (3 GB) |
| S3 Requests | None | ~$0.02/month |
| CloudFront | 1 TB, 10M requests | $0 |
| SQS | 1M requests | $0 |
| Cognito | 50K MAU | $0 |
| EventBridge | AWS events free | $0 |
| Secrets Manager | None | $2/month |

**Total Monthly Cost (After 12 Months):** ~$12-15/month

#### **Cost Mitigation Strategies**

1. **Secrets Manager → SSM Parameter Store**
   - Use encrypted SSM parameters for static API keys
   - Saves $2/month
   - Only use Secrets Manager for auto-rotating credentials

2. **Aggressive Video Compression**
   - Compress videos before upload (client-side or Lambda)
   - Target: Keep under 5 GB S3 storage

3. **CloudFront Cache Optimization**
   - Maximize cache hit ratio to minimize S3 requests
   - Use cache-control headers

4. **Lambda Optimization**
   - Use ARM64 architecture (20% cheaper)
   - Minimize package size for faster cold starts
   - Right-size memory allocation

5. **DynamoDB On-Demand Mode**
   - Only pay for actual usage
   - No wasted capacity

6. **API Gateway Caching**
   - Cache GET requests for user data (if needed)
   - Reduces Lambda invocations

#### **Potential Overages to Monitor**

⚠️ **Video Storage** - Most likely to exceed free tier
- **Risk:** High-quality videos can be 50-500 MB each
- **Mitigation:**
  - Client-side compression
  - Lifecycle policies (delete after 90 days)
  - Resolution limits (1080p max)
  - Consider transcoding to web-optimized formats

⚠️ **API Gateway** - After 12 months
- **Risk:** 1M requests = $10
- **Mitigation:**
  - Cache static data on client
  - Implement pagination
  - Use WebSockets for real-time updates (future)

⚠️ **Secrets Manager** - Ongoing cost
- **Risk:** $0.40 per secret per month
- **Mitigation:** Use SSM Parameter Store for non-rotating secrets

---

## Backend Architecture

### FastAPI Application Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + Lambda handler
│   ├── config.py            # Environment config
│   ├── dependencies.py      # Dependency injection
│   │
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py      # Authentication endpoints
│   │   │   ├── platforms.py # Platform management
│   │   │   ├── posts.py     # Post CRUD
│   │   │   ├── comments.py  # Comment management
│   │   │   └── media.py     # Media upload/management
│   │
│   ├── core/                # Business logic
│   │   ├── __init__.py
│   │   ├── security.py      # JWT validation
│   │   ├── aws.py           # AWS SDK helpers
│   │   └── exceptions.py    # Custom exceptions
│   │
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── post.py
│   │   ├── platform.py
│   │   └── comment.py
│   │
│   ├── services/            # External integrations
│   │   ├── __init__.py
│   │   ├── dynamodb.py      # DynamoDB operations
│   │   ├── s3.py            # S3 operations
│   │   ├── sqs.py           # SQS operations
│   │   ├── secrets.py       # Secrets Manager
│   │   │
│   │   └── platforms/       # Social media integrations
│   │       ├── __init__.py
│   │       ├── base.py      # Abstract base class
│   │       ├── facebook.py
│   │       ├── instagram.py
│   │       ├── youtube.py
│   │       ├── linkedin.py
│   │       └── tiktok.py
│   │
│   └── workers/             # Background workers (Lambda functions)
│       ├── __init__.py
│       ├── post_processor.py    # SQS consumer for posting
│       ├── comment_sync.py      # Scheduled comment polling
│       └── media_optimizer.py   # S3 trigger for optimization
│
├── tests/                   # Unit and integration tests
│   ├── test_api/
│   ├── test_services/
│   └── test_workers/
│
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Dev dependencies
└── template.yaml            # SAM template
```

### Core Backend Components

#### **1. Main FastAPI Application** (`app/main.py`)

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from app.api.v1 import auth, platforms, posts, comments, media
from app.core.security import get_current_user

app = FastAPI(
    title="ToAllCreation API",
    description="Gospel-focused social media aggregator",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(platforms.router, prefix="/api/v1/platforms", tags=["platforms"], dependencies=[Depends(get_current_user)])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"], dependencies=[Depends(get_current_user)])
app.include_router(comments.router, prefix="/api/v1/comments", tags=["comments"], dependencies=[Depends(get_current_user)])
app.include_router(media.router, prefix="/api/v1/media", tags=["media"], dependencies=[Depends(get_current_user)])

@app.get("/")
def root():
    return {"message": "ToAllCreation API - Spreading the Gospel"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# Lambda handler
handler = Mangum(app)
```

#### **2. Platform Integration Base Class** (`app/services/platforms/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class PlatformConfig(BaseModel):
    platform_name: str
    access_token: str
    refresh_token: Optional[str] = None
    additional_config: Dict[str, Any] = {}

class PostResult(BaseModel):
    success: bool
    platform_post_id: Optional[str] = None
    error_message: Optional[str] = None
    permalink: Optional[str] = None

class Comment(BaseModel):
    id: str
    text: str
    author: str
    timestamp: str
    platform_comment_id: str

class BasePlatform(ABC):
    """Abstract base class for social media platform integrations"""

    def __init__(self, config: PlatformConfig):
        self.config = config

    @abstractmethod
    async def post_text(self, content: str) -> PostResult:
        """Post text content to platform"""
        pass

    @abstractmethod
    async def post_image(self, content: str, image_url: str) -> PostResult:
        """Post image with caption"""
        pass

    @abstractmethod
    async def post_video(self, content: str, video_url: str) -> PostResult:
        """Post video with description"""
        pass

    @abstractmethod
    async def get_comments(self, post_id: str) -> List[Comment]:
        """Retrieve comments for a post"""
        pass

    @abstractmethod
    async def reply_to_comment(self, comment_id: str, message: str) -> bool:
        """Reply to a comment"""
        pass

    @abstractmethod
    async def validate_token(self) -> bool:
        """Validate access token"""
        pass

    @abstractmethod
    async def refresh_access_token(self) -> Optional[str]:
        """Refresh expired access token"""
        pass
```

#### **3. Facebook Integration Example** (`app/services/platforms/facebook.py`)

```python
import httpx
from typing import List, Optional
from app.services.platforms.base import BasePlatform, PostResult, Comment, PlatformConfig

class FacebookPlatform(BasePlatform):
    BASE_URL = "https://graph.facebook.com/v19.0"

    async def post_text(self, content: str) -> PostResult:
        """Post text to Facebook Page"""
        try:
            page_id = self.config.additional_config.get("page_id")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/{page_id}/feed",
                    params={
                        "message": content,
                        "access_token": self.config.access_token
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return PostResult(
                        success=True,
                        platform_post_id=data.get("id"),
                        permalink=f"https://facebook.com/{data.get('id')}"
                    )
                else:
                    return PostResult(
                        success=False,
                        error_message=response.text
                    )
        except Exception as e:
            return PostResult(success=False, error_message=str(e))

    async def post_image(self, content: str, image_url: str) -> PostResult:
        """Post image to Facebook Page"""
        try:
            page_id = self.config.additional_config.get("page_id")

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/{page_id}/photos",
                    params={
                        "url": image_url,
                        "caption": content,
                        "access_token": self.config.access_token
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return PostResult(
                        success=True,
                        platform_post_id=data.get("id"),
                        permalink=data.get("permalink_url")
                    )
                else:
                    return PostResult(success=False, error_message=response.text)
        except Exception as e:
            return PostResult(success=False, error_message=str(e))

    async def post_video(self, content: str, video_url: str) -> PostResult:
        """Post video to Facebook Page"""
        # Similar implementation using /videos endpoint
        pass

    async def get_comments(self, post_id: str) -> List[Comment]:
        """Get comments for a Facebook post"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/{post_id}/comments",
                    params={
                        "access_token": self.config.access_token,
                        "fields": "id,message,from,created_time"
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return [
                        Comment(
                            id=f"FB#{comment['id']}",
                            text=comment.get("message", ""),
                            author=comment["from"]["name"],
                            timestamp=comment["created_time"],
                            platform_comment_id=comment["id"]
                        )
                        for comment in data.get("data", [])
                    ]
        except Exception:
            return []

    async def reply_to_comment(self, comment_id: str, message: str) -> bool:
        """Reply to Facebook comment"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/{comment_id}/comments",
                    params={
                        "message": message,
                        "access_token": self.config.access_token
                    }
                )
                return response.status_code == 200
        except Exception:
            return False

    async def validate_token(self) -> bool:
        """Validate Facebook access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/me",
                    params={"access_token": self.config.access_token}
                )
                return response.status_code == 200
        except Exception:
            return False

    async def refresh_access_token(self) -> Optional[str]:
        """Facebook long-lived tokens last 60 days, need manual refresh"""
        # Implement token refresh logic
        return None
```

#### **4. Post Processing Worker** (`app/workers/post_processor.py`)

```python
import json
import boto3
from typing import Dict, Any
from app.services.platforms import get_platform_client
from app.services.dynamodb import update_post_status
from app.services.secrets import get_platform_credentials

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')

async def lambda_handler(event: Dict[str, Any], context: Any):
    """
    SQS consumer Lambda that processes post publishing to platforms
    """

    for record in event['Records']:
        message_body = json.loads(record['body'])

        post_id = message_body['post_id']
        platform = message_body['platform']
        content = message_body['content']
        media_urls = message_body.get('media_urls', [])
        user_id = message_body['user_id']

        try:
            # Get platform credentials
            credentials = await get_platform_credentials(user_id, platform)

            # Initialize platform client
            platform_client = get_platform_client(platform, credentials)

            # Post content
            if media_urls and media_urls[0].endswith(('.mp4', '.mov', '.avi')):
                result = await platform_client.post_video(content, media_urls[0])
            elif media_urls:
                result = await platform_client.post_image(content, media_urls[0])
            else:
                result = await platform_client.post_text(content)

            # Update DynamoDB
            if result.success:
                await update_post_status(
                    post_id=post_id,
                    platform=platform,
                    status="published",
                    platform_post_id=result.platform_post_id,
                    permalink=result.permalink
                )
            else:
                await update_post_status(
                    post_id=post_id,
                    platform=platform,
                    status="failed",
                    error_message=result.error_message
                )

                # Send to DLQ if max retries exceeded
                raise Exception(f"Failed to post to {platform}: {result.error_message}")

        except Exception as e:
            print(f"Error processing post {post_id} for {platform}: {str(e)}")
            # SQS will automatically retry or send to DLQ
            raise

    return {
        'statusCode': 200,
        'body': json.dumps('Posts processed successfully')
    }
```

#### **5. Comment Sync Worker** (`app/workers/comment_sync.py`)

```python
import boto3
from datetime import datetime, timedelta
from app.services.platforms import get_platform_client
from app.services.dynamodb import get_user_posts, save_comments
from app.services.secrets import get_all_platform_credentials

dynamodb = boto3.resource('dynamodb')

async def lambda_handler(event, context):
    """
    EventBridge scheduled Lambda that polls platforms for new comments
    Runs every 15 minutes
    """

    # For MVP: single user
    user_id = "USER#default"

    # Get all posts from last 7 days
    cutoff_date = datetime.utcnow() - timedelta(days=7)
    posts = await get_user_posts(user_id, since=cutoff_date)

    # Get platform credentials
    credentials = await get_all_platform_credentials(user_id)

    for post in posts:
        for platform, platform_data in post.get('platforms', {}).items():
            if platform_data.get('status') != 'published':
                continue

            platform_post_id = platform_data.get('platform_post_id')
            if not platform_post_id:
                continue

            try:
                # Initialize platform client
                client = get_platform_client(platform, credentials[platform])

                # Fetch comments
                comments = await client.get_comments(platform_post_id)

                # Save new comments to DynamoDB
                await save_comments(post['id'], platform, comments)

            except Exception as e:
                print(f"Error fetching comments for {platform} post {platform_post_id}: {str(e)}")
                continue

    return {
        'statusCode': 200,
        'body': 'Comment sync completed'
    }
```

#### **6. DynamoDB Service** (`app/services/dynamodb.py`)

```python
import boto3
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

async def save_post(user_id: str, post_data: Dict[str, Any]) -> str:
    """Save post to DynamoDB"""
    post_id = f"POST#{datetime.utcnow().timestamp()}"
    timestamp = datetime.utcnow().isoformat()

    # User's post entry
    table.put_item(Item={
        'PK': f'USER#{user_id}',
        'SK': post_id,
        'post_id': post_id,
        'content': post_data['content'],
        'media_urls': post_data.get('media_urls', []),
        'platforms': post_data['platforms'],
        'status': 'draft',
        'created_at': timestamp,
        'updated_at': timestamp
    })

    # Post metadata entry
    table.put_item(Item={
        'PK': post_id,
        'SK': 'METADATA',
        'user_id': user_id,
        'content': post_data['content'],
        'media_urls': post_data.get('media_urls', []),
        'created_at': timestamp
    })

    return post_id

async def update_post_status(
    post_id: str,
    platform: str,
    status: str,
    platform_post_id: Optional[str] = None,
    permalink: Optional[str] = None,
    error_message: Optional[str] = None
):
    """Update post status for a specific platform"""
    table.put_item(Item={
        'PK': post_id,
        'SK': f'PLATFORM#{platform}#{platform_post_id or "pending"}',
        'status': status,
        'platform_post_id': platform_post_id,
        'permalink': permalink,
        'error_message': error_message,
        'updated_at': datetime.utcnow().isoformat()
    })

async def get_user_posts(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get all posts for a user"""
    response = table.query(
        KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
        ExpressionAttributeValues={
            ':pk': f'USER#{user_id}',
            ':sk': 'POST#'
        },
        Limit=limit,
        ScanIndexForward=False  # Newest first
    )
    return response.get('Items', [])

async def save_comments(post_id: str, platform: str, comments: List[Any]):
    """Save comments to DynamoDB"""
    for comment in comments:
        table.put_item(Item={
            'PK': post_id,
            'SK': f'COMMENT#{comment.id}',
            'platform': platform,
            'text': comment.text,
            'author': comment.author,
            'timestamp': comment.timestamp,
            'platform_comment_id': comment.platform_comment_id,
            'created_at': datetime.utcnow().isoformat()
        })
```

---

## Frontend Architecture

### React Application Structure

```
frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
│
├── src/
│   ├── main.tsx                  # Entry point
│   ├── App.tsx                   # Main app component
│   │
│   ├── components/               # Reusable components
│   │   ├── ui/                   # Shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── Footer.tsx
│   │   │
│   │   ├── post/
│   │   │   ├── PostComposer.tsx      # Main post creation
│   │   │   ├── PostCard.tsx          # Display post
│   │   │   ├── PostList.tsx
│   │   │   ├── MediaUploader.tsx
│   │   │   └── PlatformSelector.tsx
│   │   │
│   │   ├── platform/
│   │   │   ├── PlatformCard.tsx
│   │   │   ├── PlatformConnect.tsx
│   │   │   └── OAuthCallback.tsx
│   │   │
│   │   └── comment/
│   │       ├── CommentList.tsx
│   │       ├── CommentCard.tsx
│   │       └── CommentReply.tsx
│   │
│   ├── pages/                    # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Login.tsx
│   │   ├── Posts.tsx
│   │   ├── CreatePost.tsx
│   │   ├── Comments.tsx
│   │   ├── Platforms.tsx
│   │   └── Settings.tsx
│   │
│   ├── store/                    # Zustand stores
│   │   ├── authStore.ts
│   │   ├── postStore.ts
│   │   ├── platformStore.ts
│   │   └── commentStore.ts
│   │
│   ├── api/                      # API client
│   │   ├── client.ts             # Axios instance
│   │   ├── auth.ts
│   │   ├── posts.ts
│   │   ├── platforms.ts
│   │   ├── comments.ts
│   │   └── media.ts
│   │
│   ├── hooks/                    # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── usePosts.ts
│   │   ├── usePlatforms.ts
│   │   └── useMediaUpload.ts
│   │
│   ├── utils/                    # Utility functions
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   └── constants.ts
│   │
│   ├── types/                    # TypeScript types
│   │   ├── post.ts
│   │   ├── platform.ts
│   │   ├── comment.ts
│   │   └── user.ts
│   │
│   └── styles/                   # Global styles
│       └── globals.css
│
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
└── .env.local
```

### Key Frontend Components

#### **1. Zustand Store - Posts** (`src/store/postStore.ts`)

```typescript
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface Media {
  url: string
  type: 'image' | 'video'
}

interface Post {
  id: string
  content: string
  media: Media[]
  platforms: string[]
  status: 'draft' | 'scheduled' | 'publishing' | 'published' | 'failed'
  platformStatuses: Record<string, {
    status: string
    postId?: string
    permalink?: string
    error?: string
  }>
  createdAt: string
  publishedAt?: string
}

interface PostStore {
  posts: Post[]
  currentPost: Partial<Post> | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchPosts: () => Promise<void>
  createPost: (post: Partial<Post>) => Promise<void>
  updatePost: (id: string, updates: Partial<Post>) => Promise<void>
  deletePost: (id: string) => Promise<void>
  publishPost: (id: string) => Promise<void>
  setCurrentPost: (post: Partial<Post> | null) => void
}

export const usePostStore = create<PostStore>()(
  devtools(
    persist(
      (set, get) => ({
        posts: [],
        currentPost: null,
        isLoading: false,
        error: null,

        fetchPosts: async () => {
          set({ isLoading: true, error: null })
          try {
            const response = await fetch('/api/v1/posts', {
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })
            const data = await response.json()
            set({ posts: data, isLoading: false })
          } catch (error) {
            set({ error: error.message, isLoading: false })
          }
        },

        createPost: async (post) => {
          set({ isLoading: true, error: null })
          try {
            const response = await fetch('/api/v1/posts', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              },
              body: JSON.stringify(post)
            })
            const newPost = await response.json()
            set(state => ({
              posts: [newPost, ...state.posts],
              isLoading: false
            }))
          } catch (error) {
            set({ error: error.message, isLoading: false })
          }
        },

        publishPost: async (id) => {
          set({ isLoading: true, error: null })
          try {
            await fetch(`/api/v1/posts/${id}/publish`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
              }
            })
            // Optimistic update
            set(state => ({
              posts: state.posts.map(p =>
                p.id === id ? { ...p, status: 'publishing' } : p
              ),
              isLoading: false
            }))
          } catch (error) {
            set({ error: error.message, isLoading: false })
          }
        },

        setCurrentPost: (post) => set({ currentPost: post })
      }),
      { name: 'post-storage' }
    )
  )
)
```

#### **2. Post Composer Component** (`src/components/post/PostComposer.tsx`)

```typescript
import React, { useState } from 'react'
import { usePostStore } from '@/store/postStore'
import { usePlatformStore } from '@/store/platformStore'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card } from '@/components/ui/card'
import { MediaUploader } from './MediaUploader'
import { PlatformSelector } from './PlatformSelector'

export const PostComposer: React.FC = () => {
  const [content, setContent] = useState('')
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [media, setMedia] = useState<any[]>([])

  const { createPost, publishPost } = usePostStore()
  const { connectedPlatforms } = usePlatformStore()

  const handleCreateDraft = async () => {
    await createPost({
      content,
      platforms: selectedPlatforms,
      media,
      status: 'draft'
    })
  }

  const handlePublishNow = async () => {
    const post = await createPost({
      content,
      platforms: selectedPlatforms,
      media,
      status: 'draft'
    })
    await publishPost(post.id)
  }

  const characterCount = content.length
  const maxChars = 280 // Twitter limit as reference

  return (
    <Card className="p-6">
      <h2 className="text-2xl font-bold mb-4">Create Post</h2>

      <Textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder="Share the gospel message..."
        className="min-h-[150px] mb-4"
      />

      <div className="text-sm text-gray-500 mb-4">
        {characterCount} characters
      </div>

      <MediaUploader
        media={media}
        onMediaChange={setMedia}
        className="mb-4"
      />

      <PlatformSelector
        platforms={connectedPlatforms}
        selected={selectedPlatforms}
        onChange={setSelectedPlatforms}
        className="mb-4"
      />

      <div className="flex gap-2">
        <Button onClick={handleCreateDraft} variant="outline">
          Save Draft
        </Button>
        <Button
          onClick={handlePublishNow}
          disabled={!content || selectedPlatforms.length === 0}
        >
          Publish Now
        </Button>
      </div>
    </Card>
  )
}
```

#### **3. Media Upload Hook** (`src/hooks/useMediaUpload.ts`)

```typescript
import { useState } from 'react'
import axios from 'axios'

interface UploadProgress {
  percent: number
  file: File
}

export const useMediaUpload = () => {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState<UploadProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const uploadMedia = async (file: File): Promise<string> => {
    setUploading(true)
    setError(null)
    setProgress({ percent: 0, file })

    try {
      // Step 1: Get pre-signed upload URL from backend
      const { data } = await axios.get('/api/v1/media/upload-url', {
        params: {
          filename: file.name,
          contentType: file.type
        },
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      const { uploadUrl, fileUrl } = data

      // Step 2: Upload directly to S3 with progress tracking
      await axios.put(uploadUrl, file, {
        headers: {
          'Content-Type': file.type
        },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          )
          setProgress({ percent, file })
        }
      })

      setUploading(false)
      setProgress(null)

      return fileUrl

    } catch (err) {
      setError(err.message)
      setUploading(false)
      throw err
    }
  }

  return {
    uploadMedia,
    uploading,
    progress,
    error
  }
}
```

#### **4. OAuth Callback Handler** (`src/components/platform/OAuthCallback.tsx`)

```typescript
import React, { useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { usePlatformStore } from '@/store/platformStore'

export const OAuthCallback: React.FC = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { completePlatformConnection } = usePlatformStore()

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code')
      const state = searchParams.get('state')
      const error = searchParams.get('error')

      if (error) {
        console.error('OAuth error:', error)
        navigate('/platforms?error=' + error)
        return
      }

      if (!code || !state) {
        navigate('/platforms?error=missing_params')
        return
      }

      try {
        // Parse state to get platform name
        const { platform } = JSON.parse(atob(state))

        // Send code to backend to exchange for access token
        await completePlatformConnection(platform, code)

        navigate('/platforms?success=true')
      } catch (err) {
        console.error('Error completing OAuth:', err)
        navigate('/platforms?error=auth_failed')
      }
    }

    handleCallback()
  }, [searchParams, navigate, completePlatformConnection])

  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4"></div>
        <p>Connecting platform...</p>
      </div>
    </div>
  )
}
```

---

## Security & Authentication

### Authentication Flow

```
1. User visits app → Redirected to Cognito Hosted UI
2. User logs in → Cognito issues JWT tokens (ID, Access, Refresh)
3. Frontend stores tokens in localStorage/sessionStorage
4. API requests include Authorization: Bearer <token>
5. API Gateway validates JWT against Cognito
6. Lambda receives validated user info in event.requestContext.authorizer
7. Token refresh handled automatically by frontend when expired
```

### Security Best Practices

#### **1. Cognito Configuration**

- **Password Policy:**
  - Minimum 8 characters
  - Require uppercase, lowercase, number, special character
  - Password expiration: Optional (90 days)

- **MFA:**
  - Use TOTP (Time-based One-Time Password) authenticator apps
  - Avoid SMS MFA (costs per message)

- **Account Recovery:**
  - Email-based recovery (free via Cognito)
  - Security questions (optional)

- **Advanced Security:**
  - Enable Cognito Advanced Security (risk-based adaptive auth)
  - Only available in Plus tier ($$$)
  - **Recommendation:** Skip for MVP, add in Phase 2 if needed

#### **2. API Security**

- **HTTPS Only:** Enforce SSL/TLS via CloudFront and API Gateway
- **CORS:** Restrict origins to production domain
- **Rate Limiting:** API Gateway throttling (10,000 req/sec default)
- **Input Validation:** Pydantic models validate all inputs
- **SQL Injection:** N/A (using DynamoDB, not SQL)
- **XSS Protection:** React escapes outputs by default

#### **3. Secrets Management**

**Social Media API Tokens:**
- Store in AWS Secrets Manager (encrypted at rest)
- Rotate tokens before expiration (Lambda function)
- Use IAM roles for Lambda to access secrets (no hardcoded creds)

**Example Secrets Structure:**
```json
{
  "facebook": {
    "access_token": "EAAxxxxx",
    "page_id": "123456789",
    "expires_at": "2025-12-01T00:00:00Z"
  },
  "instagram": {
    "access_token": "IGQxxxxx",
    "account_id": "987654321",
    "expires_at": "2025-12-01T00:00:00Z"
  }
}
```

**Access Pattern:**
```python
import boto3
import json

secrets_client = boto3.client('secretsmanager')

def get_platform_credentials(user_id: str, platform: str):
    secret_name = f"toallcreation/{user_id}/platforms"
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secrets = json.loads(response['SecretString'])
    return secrets.get(platform)
```

#### **4. IAM Roles and Policies**

**Lambda Execution Role:**
```yaml
Policies:
  - DynamoDBCrudPolicy:
      TableName: !Ref ToAllCreationTable
  - S3CrudPolicy:
      BucketName: !Ref MediaBucket
  - SQSSendMessagePolicy:
      QueueName: !Ref PostQueue
  - SecretsManagerReadWrite:
      SecretArn: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:toallcreation/*"
  - CloudWatchLogsFullAccess
```

**Frontend S3 Bucket Policy (CloudFront Access):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::toallcreation-frontend/*"
    }
  ]
}
```

#### **5. Data Encryption**

- **At Rest:**
  - DynamoDB: AWS-managed encryption (default)
  - S3: SSE-S3 (server-side encryption)
  - Secrets Manager: AWS KMS encryption

- **In Transit:**
  - HTTPS everywhere (CloudFront, API Gateway)
  - TLS 1.2+ only

#### **6. Monitoring & Logging**

- **CloudWatch Logs:** All Lambda function logs
- **API Gateway Logs:** Request/response logging (disabled for cost)
- **DynamoDB Streams:** Track data changes
- **CloudTrail:** API audit trail (optional, costs extra)

**Alerts:**
- Failed authentication attempts
- API errors (5xx responses)
- DynamoDB throttling
- S3 storage approaching limits

---

## CI/CD Pipeline

### GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`

```yaml
name: Deploy ToAllCreation

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main

env:
  AWS_REGION: us-east-1
  PYTHON_VERSION: "3.12"
  NODE_VERSION: "20"

jobs:
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        working-directory: ./backend
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        working-directory: ./backend
        run: |
          pytest tests/ --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./backend/coverage.xml

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Run linter
        working-directory: ./frontend
        run: npm run lint

      - name: Run tests
        working-directory: ./frontend
        run: npm test

      - name: Build
        working-directory: ./frontend
        run: npm run build

  deploy-backend:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Set up SAM CLI
        uses: aws-actions/setup-sam@v2

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Build SAM application
        working-directory: ./backend
        run: sam build --use-container

      - name: Deploy to AWS
        working-directory: ./backend
        run: |
          sam deploy \
            --no-confirm-changeset \
            --no-fail-on-empty-changeset \
            --stack-name toallcreation-backend \
            --capabilities CAPABILITY_IAM \
            --parameter-overrides Environment=production

  deploy-frontend:
    runs-on: ubuntu-latest
    needs: [test-backend, test-frontend]
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

    permissions:
      id-token: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}

      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Build production bundle
        working-directory: ./frontend
        run: npm run build
        env:
          VITE_API_URL: ${{ secrets.VITE_API_URL }}

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Sync to S3
        working-directory: ./frontend
        run: |
          aws s3 sync dist/ s3://toallcreation-frontend --delete

      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"
```

### Deployment Strategy

#### **Environments:**

1. **Development (`develop` branch)**
   - Auto-deploy on push
   - Separate AWS stack
   - Use separate DynamoDB table
   - Lower Lambda memory for cost savings

2. **Production (`main` branch)**
   - Auto-deploy on push to main
   - Requires PR approval
   - Production AWS stack
   - Production DynamoDB table

#### **Deployment Steps:**

1. **Backend Deployment:**
   - Run tests
   - Build SAM application
   - Package Lambda functions
   - Deploy CloudFormation stack
   - Update Lambda functions
   - ~3-5 minutes

2. **Frontend Deployment:**
   - Run tests and linting
   - Build production bundle (Vite)
   - Sync to S3 bucket
   - Invalidate CloudFront cache
   - ~2-3 minutes

#### **Rollback Strategy:**

- **Backend:** CloudFormation rollback on failure
- **Frontend:** S3 versioning + revert to previous version
- **Database:** DynamoDB point-in-time recovery (if enabled)

---

## Cost Analysis & Free Tier Strategy

### Detailed Cost Breakdown

#### **First 12 Months (AWS Free Tier Active)**

| Service | Free Tier | Expected Usage | Cost |
|---------|-----------|----------------|------|
| **Lambda** | 1M requests/mo, 400K GB-sec | 10K API requests, 100K async | $0 |
| **API Gateway (HTTP)** | 1M requests/mo | 10K requests/mo | $0 |
| **DynamoDB** | 25 GB, 25 WCU/RCU | 1 GB, ~5 WCU/RCU | $0 |
| **S3 Storage** | 5 GB | 3 GB (videos compressed) | $0 |
| **S3 Requests** | 20K GET, 2K PUT | 5K GET, 500 PUT | $0 |
| **CloudFront** | 1 TB, 10M req | 50 GB, 500K req | $0 |
| **SQS** | 1M requests/mo | 100K requests/mo | $0 |
| **Cognito** | 50K MAU | 1 user | $0 |
| **EventBridge** | AWS events free | 3K scheduled events | $0 |
| **Secrets Manager** | $200 credit (6-12 mo) | 5 secrets @ $0.40/secret | **$2/mo** |
| **Route 53** (optional) | N/A | 1 hosted zone | **$0.50/mo** |
| **ACM** | Free | 2 certificates | $0 |
| **Data Transfer** | 100 GB/mo | 20 GB/mo | $0 |

**Monthly Total (First 12 Months):** ~$2-3/month

#### **After 12 Months (Permanent Free Tier)**

| Service | Permanent Free Tier | Expected Usage | Cost After 12 Mo |
|---------|---------------------|----------------|------------------|
| **Lambda** | 1M req, 400K GB-sec | 10K requests | $0 |
| **API Gateway** | None | 10K requests | **$0.01** (negligible) |
| **DynamoDB** | 25 GB, 25 WCU/RCU | 1 GB, ~5 WCU/RCU | $0 |
| **S3 Storage** | None | 3 GB @ $0.023/GB | **$0.07** |
| **S3 Requests** | None | 5K GET, 500 PUT | **$0.02** |
| **CloudFront** | 1 TB, 10M req | 50 GB, 500K req | $0 |
| **SQS** | 1M requests | 100K requests | $0 |
| **Cognito** | 50K MAU | 1 user | $0 |
| **EventBridge** | AWS events free | 3K events | $0 |
| **Secrets Manager** | None | 5 secrets | **$2.00** |
| **Route 53** | N/A | 1 hosted zone | **$0.50** |

**Monthly Total (After 12 Months):** ~$2.60/month

**Annual Cost (After 12 Months):** ~$31/year

### Cost Optimization Strategies

#### **1. Replace Secrets Manager with SSM Parameter Store**

**Savings:** $2/month → $0/month

```python
# Use SSM Parameter Store for static secrets
import boto3

ssm = boto3.client('ssm')

# Store secret (one-time)
ssm.put_parameter(
    Name='/toallcreation/facebook/app-secret',
    Value='secret-value',
    Type='SecureString',  # Encrypted with KMS
    Tier='Standard'  # Free tier
)

# Retrieve secret
response = ssm.get_parameter(
    Name='/toallcreation/facebook/app-secret',
    WithDecryption=True
)
secret = response['Parameter']['Value']
```

**Trade-off:** No automatic rotation, manual management

**Recommendation:** Use SSM for app secrets, Secrets Manager only if auto-rotation is critical

#### **2. Aggressive Video Compression**

**Problem:** Videos can be 50-500 MB each, exceeding 5 GB S3 free tier quickly

**Solutions:**

a. **Client-Side Compression (Browser)**
```typescript
// Use browser-image-compression library
import imageCompression from 'browser-image-compression'

const compressVideo = async (file: File) => {
  const options = {
    maxSizeMB: 10,
    maxWidthOrHeight: 1920,
    useWebWorker: true
  }
  return await imageCompression(file, options)
}
```

b. **Lambda Video Optimization (S3 Trigger)**
```python
# Use FFmpeg in Lambda Layer
import subprocess

def optimize_video(input_path, output_path):
    subprocess.run([
        'ffmpeg',
        '-i', input_path,
        '-vcodec', 'h264',
        '-crf', '28',  # Constant Rate Factor (quality)
        '-preset', 'fast',
        '-vf', 'scale=1280:-2',  # 720p
        output_path
    ])
```

c. **Lifecycle Policies**
```yaml
# SAM template
MediaBucket:
  Type: AWS::S3::Bucket
  Properties:
    LifecycleConfiguration:
      Rules:
        - Id: DeleteOldVideos
          Status: Enabled
          ExpirationInDays: 90  # Delete after 90 days
        - Id: MoveToIA
          Status: Enabled
          Transitions:
            - StorageClass: STANDARD_IA
              TransitionInDays: 30
```

**Estimated Savings:** Keep S3 under 5 GB free tier

#### **3. Caching Strategy**

**CloudFront Caching:**
- Frontend assets: 1 year (immutable URLs)
- API responses: Use sparingly (data freshness)
- Media files: 1 year

**React Query Caching:**
```typescript
import { QueryClient } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false
    }
  }
})
```

**Benefit:** Reduces API Gateway + Lambda invocations

#### **4. Lambda Optimization**

**ARM64 Architecture:**
```yaml
Function:
  Type: AWS::Serverless::Function
  Properties:
    Runtime: python3.12
    Architecture: arm64  # 20% cheaper, 20% faster
```

**Right-Sizing Memory:**
- Default: 512 MB (balance cost/performance)
- API handlers: 256-512 MB
- Video processing: 1024-2048 MB (only if needed)

**Lambda Layers:**
```yaml
SharedLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: shared-dependencies
    ContentUri: layers/shared/
    CompatibleRuntimes:
      - python3.12
```

**Benefit:** Reduce deployment package size, faster cold starts

#### **5. Monitor Usage**

**AWS Budgets:**
- Set budget alert at $5/month
- Get notified at 80% and 100% thresholds

**CloudWatch Alarms:**
- S3 storage > 4.5 GB
- Lambda invocations > 900K/month
- DynamoDB consumed capacity > 80%

---

## Implementation Roadmap

### Phase 1: MVP (Weeks 1-8)

#### **Week 1-2: Foundation & Setup**

**Tasks:**
1. Initialize Git repository
2. Set up AWS account and configure IAM
3. Create GitHub repository
4. Set up development environment
   - Install AWS CLI, SAM CLI
   - Configure VS Code with extensions
5. Initialize project structure
   - Backend: `sam init` with Python
   - Frontend: `npm create vite@latest`
6. Set up GitHub Actions workflows (basic)
7. Create DynamoDB table (via SAM)
8. Set up Cognito User Pool
9. Create S3 buckets (frontend, media)
10. Configure CloudFront distributions

**Deliverables:**
- Working AWS infrastructure
- Empty frontend and backend scaffolds
- CI/CD pipeline (basic)

#### **Week 3-4: Authentication & Backend Core**

**Tasks:**
1. Implement Cognito authentication
   - Hosted UI setup
   - JWT validation in API Gateway
2. Build FastAPI application structure
   - Main app with Mangum
   - Health check endpoint
   - Error handling
3. Create DynamoDB service layer
   - CRUD operations
   - Single-table design implementation
4. Implement platform management API
   - Get connected platforms
   - Connect platform (OAuth initiation)
   - Disconnect platform
5. Create Secrets Manager/SSM integration
   - Store/retrieve platform tokens
6. Unit tests for backend

**Deliverables:**
- Working authentication system
- Platform management API
- 70%+ test coverage

#### **Week 5-6: Social Media Integrations**

**Tasks:**
1. Implement Facebook integration
   - OAuth flow
   - Post text, image, video
   - Validate token
2. Implement Instagram integration
   - Business account setup
   - Post text, image, reels
3. Implement YouTube integration
   - OAuth flow
   - Video upload
   - Quota management
4. Create SQS post queue
5. Implement post processor Lambda
   - SQS consumer
   - Platform posting logic
   - Error handling and DLQ
6. Integration tests

**Deliverables:**
- Working Facebook, Instagram, YouTube posting
- Async job processing
- Error handling and retry logic

#### **Week 7-8: Frontend & UI**

**Tasks:**
1. Set up React app structure
   - Router configuration
   - Zustand stores
   - API client with Axios
2. Implement authentication UI
   - Login page
   - OAuth callback handler
   - Protected routes
3. Build platform management UI
   - Platform cards
   - Connect/disconnect buttons
   - OAuth flow
4. Create post composer
   - Rich text editor
   - Platform selector
   - Media uploader (S3 pre-signed URLs)
5. Build post dashboard
   - Post list
   - Post status tracking
   - Platform-specific statuses
6. Deploy frontend to S3/CloudFront
7. End-to-end testing

**Deliverables:**
- Fully functional web UI
- End-to-end posting workflow
- Deployed production app

**MVP Success Criteria:**
- ✅ User can log in
- ✅ User can connect Facebook, Instagram, YouTube
- ✅ User can create post with text
- ✅ User can upload image/video
- ✅ User can publish to selected platforms simultaneously
- ✅ User can see post status per platform
- ✅ System stays within AWS Free Tier

---

### Phase 2: Comment Aggregation (Weeks 9-12)

#### **Week 9-10: Comment Infrastructure**

**Tasks:**
1. Implement comment polling for Facebook
   - Webhooks setup (if available)
   - Polling fallback
2. Implement comment polling for Instagram
   - Limited webhook support
3. Implement comment polling for YouTube
   - Comments API integration
4. Create EventBridge scheduled rule (every 15 min)
5. Implement comment sync Lambda
   - Poll all platforms
   - Store comments in DynamoDB
   - DynamoDB Streams for notifications
6. Build comment reply API
   - Reply to Facebook comment
   - Reply to Instagram comment
   - Reply to YouTube comment

**Deliverables:**
- Comment aggregation working
- Real-time comment sync (15-min intervals)
- Reply functionality

#### **Week 11-12: Comment UI & Notifications**

**Tasks:**
1. Build comment dashboard UI
   - Unified comment feed
   - Filter by platform
   - Filter by post
2. Implement comment reply UI
   - Reply form
   - Threading (if supported)
3. Add notifications
   - Email notifications for new comments (SES)
   - In-app notifications (polling or WebSocket)
4. Testing and bug fixes
5. Documentation

**Deliverables:**
- Comment dashboard
- Reply functionality
- Notifications

**Phase 2 Success Criteria:**
- ✅ User sees aggregated comments from all platforms
- ✅ User can reply to comments from within app
- ✅ User receives notifications for new comments
- ✅ System stays within AWS Free Tier

---

### Phase 3: Future Enhancements (Post-MVP)

#### **Weeks 13+**

1. **LinkedIn & TikTok Support**
   - Additional platform integrations
   - Expand posting capabilities

2. **Scheduled Posting**
   - Schedule posts for future
   - Timezone support
   - Recurring posts

3. **Analytics Dashboard**
   - Engagement metrics (likes, shares, comments)
   - Reach and impressions
   - Platform comparison

4. **Donation System**
   - Stripe integration
   - Donation tracking
   - Donor management

5. **Multi-User Support**
   - Team accounts
   - User roles and permissions
   - Collaboration features

6. **Mobile Apps (Flutter)**
   - iOS app
   - Android app
   - Cross-platform codebase

7. **Advanced Features**
   - AI-powered post suggestions
   - Content calendar
   - Hashtag recommendations
   - Image/video editing

---

## Technical Decisions Requiring Input

### Critical Decisions for User Review

#### **1. Social Media Platforms**

**Question:** Which platforms are MUST-HAVE for MVP?

**Options:**
- ✅ **Facebook** (recommended - easiest, most reliable)
- ✅ **YouTube** (recommended - essential for video)
- ⚠️ **Instagram** (recommended but complex - requires business account)
- ❓ **LinkedIn** (professional audience, requires approval)
- ❓ **TikTok** (short-form video, newer API)
- ❌ **X/Twitter** (NOT recommended - $100/month minimum cost)

**Recommendation:** Start with Facebook + YouTube, add Instagram if feasible

**User Decision Needed:**
- [ ] Confirm platform priorities
- [ ] Willing to set up Instagram Business account?
- [ ] Budget for Twitter/X ($100/month) - Yes/No?

---

#### **2. Video Storage Strategy**

**Question:** How to manage video storage within 5 GB S3 free tier?

**Options:**

**Option A: Client-Side Compression (RECOMMENDED)**
- ✅ Compress videos in browser before upload
- ✅ Zero AWS costs
- ❌ User experience (wait time)
- ❌ Limited compression quality

**Option B: Lambda Video Optimization**
- ✅ Better compression quality (FFmpeg)
- ✅ Transparent to user
- ❌ Requires Lambda Layer with FFmpeg (~100 MB)
- ❌ Higher Lambda costs (memory + execution time)

**Option C: Lifecycle Policies + Compression**
- ✅ Hybrid approach
- ✅ Delete videos after 90 days
- ✅ Move to cheaper storage after 30 days
- ❌ Videos deleted after 90 days

**Option D: External Video Hosting**
- ✅ Use YouTube/Vimeo for long-term storage
- ✅ Zero S3 costs
- ❌ Dependency on third-party
- ❌ Complex workflow

**Recommendation:** Option C (Lifecycle + Compression)

**User Decision Needed:**
- [ ] Is deleting videos after 90 days acceptable?
- [ ] Maximum acceptable video size/resolution?
- [ ] Preferred compression approach?

---

#### **3. Secrets Management**

**Question:** Use AWS Secrets Manager ($2/month) or SSM Parameter Store (free)?

**Comparison:**

| Feature | Secrets Manager | SSM Parameter Store |
|---------|-----------------|---------------------|
| **Cost** | $0.40/secret/month | Free (Standard) |
| **Automatic Rotation** | ✅ Yes | ❌ No |
| **Encryption** | ✅ KMS | ✅ KMS |
| **Versioning** | ✅ Yes | ✅ Yes |
| **Cross-Region** | ✅ Yes | ❌ No |

**Recommendation:**
- Use **SSM Parameter Store** for static secrets (app IDs, client secrets)
- Use **Secrets Manager** only for auto-rotating credentials (if needed)
- **Savings:** $2/month

**User Decision Needed:**
- [ ] Acceptable to manually rotate tokens (every 60 days)?
- [ ] Or prefer automatic rotation ($2/month)?

---

#### **4. Custom Domain**

**Question:** Use custom domain or AWS-provided URLs?

**Options:**

**Option A: Custom Domain (toallcreation.com)**
- ✅ Professional appearance
- ✅ Better branding
- ❌ Costs: $12/year (domain) + $0.50/month (Route 53) = ~$18/year
- ❌ DNS configuration required

**Option B: AWS-Provided URLs**
- ✅ Free
- ✅ Zero configuration
- ❌ Ugly URLs (e.g., `d1234abcd.cloudfront.net`, `abc123.execute-api.us-east-1.amazonaws.com`)
- ❌ Less professional

**Recommendation:** Custom domain for production, AWS URLs for development

**User Decision Needed:**
- [ ] Purchase custom domain?
- [ ] Domain name preference?

---

#### **5. Email Service for Cognito**

**Question:** Use Cognito email (50/day) or Amazon SES (50,000/month)?

**Comparison:**

| Service | Free Tier | Cost After | Setup Complexity |
|---------|-----------|------------|------------------|
| **Cognito Email** | 50 emails/day | N/A (limit) | ✅ Zero config |
| **Amazon SES** | 50K emails/month (from EC2) | $0.10/1K emails | ⚠️ Domain verification required |

**Recommendation:** Start with Cognito email (sufficient for single user)

**User Decision Needed:**
- [ ] Expected email volume (password reset, notifications)?
- [ ] Need more than 50 emails/day?

---

#### **6. Development Workflow**

**Question:** Local development strategy for AWS services?

**Options:**

**Option A: LocalStack (Community Edition)**
- ✅ Emulate AWS services locally
- ✅ Free for core services
- ❌ Limited features (Pro features cost money)
- ❌ Not 100% parity with AWS

**Option B: AWS SAM Local**
- ✅ Official AWS tool
- ✅ Test Lambda functions locally
- ✅ Invoke API Gateway locally
- ❌ Still connects to real AWS for DynamoDB, S3, etc.

**Option C: Direct AWS Development Stack**
- ✅ 100% production parity
- ✅ Simple workflow
- ❌ Requires AWS account
- ❌ Potential costs (minimal with free tier)

**Recommendation:** Option C (separate dev AWS stack) - simplest and most reliable

**User Decision Needed:**
- [ ] Preference for local development setup?
- [ ] Comfortable with direct AWS development?

---

#### **7. Monitoring & Alerting**

**Question:** What level of monitoring is needed?

**Options:**

**Option A: Basic CloudWatch Logs**
- ✅ Free
- ✅ Sufficient for MVP
- ❌ Manual log review

**Option B: CloudWatch Alarms + SNS**
- ✅ Automated alerts
- ✅ Email/SMS notifications
- ❌ SMS costs $0.75/message (use email instead)

**Option C: Third-Party (Datadog, New Relic, Sentry)**
- ✅ Advanced features
- ✅ Better UX
- ❌ Costs money

**Recommendation:** Option B (CloudWatch Alarms with email via SNS)

**User Decision Needed:**
- [ ] Email for alerts?
- [ ] Critical events to monitor?

---

#### **8. Testing Strategy**

**Question:** What level of test coverage is needed?

**Options:**

**Option A: Minimal (Critical Paths Only)**
- ✅ Fast development
- ❌ Higher bug risk

**Option B: Moderate (70%+ Coverage)**
- ✅ Good balance
- ✅ Catch most bugs
- ⚠️ Some development overhead

**Option C: Comprehensive (90%+ Coverage)**
- ✅ Very reliable
- ❌ Significant development time

**Recommendation:** Option B (70%+ coverage for backend, 50%+ for frontend)

**User Decision Needed:**
- [ ] Acceptable test coverage level?
- [ ] Priority: speed vs. reliability?

---

## Challenges & Mitigation Strategies

### Anticipated Challenges

#### **1. Instagram Business Account Requirement**

**Challenge:**
- Instagram API requires Business or Creator account
- Must be linked to Facebook Page
- Business verification may be required

**Mitigation:**
1. Create Facebook Page for ministry
2. Convert Instagram to Business account
3. Link Instagram to Facebook Page
4. Follow Meta's verification process
5. **Fallback:** Skip Instagram for MVP if too complex

**Estimated Time:** 2-3 days

---

#### **2. YouTube API Quota Limits**

**Challenge:**
- YouTube quota: 10,000 units/day
- Video upload: 1,600 units
- Approximately 6 uploads/day max

**Mitigation:**
1. Request quota increase from Google (if needed)
2. Implement quota tracking in application
3. Warn user when approaching daily limit
4. Queue uploads for next day if quota exceeded
5. **Workaround:** Manual uploads for high-volume days

**Estimated Impact:** Low (6 uploads/day sufficient for MVP)

---

#### **3. OAuth Token Expiration**

**Challenge:**
- Access tokens expire (60 days for Facebook, varies by platform)
- User must re-authenticate
- Silent failures if token expired

**Mitigation:**
1. Implement token refresh logic
2. Store refresh tokens securely
3. Proactive refresh before expiration
4. Email user when re-auth required
5. Graceful error handling with user notification

**Implementation:**
```python
async def ensure_valid_token(platform_config):
    """Refresh token if expired or expiring soon"""
    expires_at = platform_config.get('expires_at')

    # Refresh if expiring within 7 days
    if datetime.now() + timedelta(days=7) > expires_at:
        new_token = await refresh_platform_token(platform_config)
        await update_stored_token(new_token)
        return new_token

    return platform_config['access_token']
```

---

#### **4. Video File Size & Upload Time**

**Challenge:**
- Large video files (50-500 MB)
- Slow uploads from browser
- Lambda timeout (15 min max)

**Mitigation:**
1. **Pre-signed S3 URLs:** Direct browser-to-S3 upload
2. **Multipart Upload:** For files > 100 MB
3. **Client-side Compression:** Reduce file size before upload
4. **Progress Indicators:** Show upload progress to user
5. **Background Processing:** Lambda triggered by S3 event (after upload completes)

**Implementation:**
```python
# Backend: Generate pre-signed upload URL
import boto3

s3 = boto3.client('s3')

def get_upload_url(filename, content_type):
    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'toallcreation-media',
            'Key': f'uploads/{filename}',
            'ContentType': content_type
        },
        ExpiresIn=3600  # 1 hour
    )
    return url
```

```typescript
// Frontend: Upload directly to S3
const uploadToS3 = async (file: File, uploadUrl: string) => {
  await axios.put(uploadUrl, file, {
    headers: {
      'Content-Type': file.type
    },
    onUploadProgress: (progressEvent) => {
      const percent = Math.round(
        (progressEvent.loaded * 100) / (progressEvent.total || 100)
      )
      setUploadProgress(percent)
    }
  })
}
```

---

#### **5. Rate Limiting Across Platforms**

**Challenge:**
- Different rate limits per platform
- Simultaneous posting may trigger limits
- Burst posting can cause failures

**Mitigation:**
1. **Sequential Posting:** Post to platforms one at a time (not parallel)
2. **Rate Limit Tracking:** Track API calls per platform
3. **Exponential Backoff:** Retry with increasing delays
4. **User Warnings:** Notify user of platform-specific limits
5. **SQS Delay:** Add delay between platform posts

**Implementation:**
```python
import asyncio

async def post_to_platforms(content, platforms):
    """Post to platforms sequentially with delays"""
    results = {}

    for platform in platforms:
        try:
            result = await post_to_platform(platform, content)
            results[platform] = result

            # Delay between platforms (avoid rate limits)
            await asyncio.sleep(2)

        except RateLimitError as e:
            # Exponential backoff
            for retry in range(3):
                await asyncio.sleep(2 ** retry)
                try:
                    result = await post_to_platform(platform, content)
                    results[platform] = result
                    break
                except RateLimitError:
                    continue

    return results
```

---

#### **6. Comment Polling Limitations**

**Challenge:**
- Most platforms don't support webhooks for comments
- Polling required (15-min intervals)
- Not real-time
- May miss comments between polls

**Mitigation:**
1. **Frequent Polling:** Every 5-15 minutes (balance cost vs. freshness)
2. **Platform Webhooks:** Use when available (Facebook)
3. **User Expectations:** Set expectation that comments sync every 15 min
4. **Manual Refresh:** Allow user to trigger sync manually
5. **Phase 2 Enhancement:** Consider third-party real-time services (costs money)

---

#### **7. AWS Free Tier Overages**

**Challenge:**
- Video storage exceeds 5 GB S3 free tier
- API calls exceed free tier after 12 months
- Unexpected costs

**Mitigation:**
1. **AWS Budgets:** Set budget alerts at $5/month
2. **Monitoring:** Track S3 storage, API calls, Lambda invocations
3. **Lifecycle Policies:** Delete old videos automatically
4. **Compression:** Aggressive video compression
5. **User Limits:** Limit video uploads (e.g., 10/month)
6. **Cost Dashboard:** Show user their usage

**Monitoring Dashboard:**
```python
# Lambda function to track usage
import boto3

cloudwatch = boto3.client('cloudwatch')

def get_monthly_usage():
    return {
        's3_storage_gb': get_s3_bucket_size(),
        'lambda_invocations': get_lambda_invocations(),
        'api_requests': get_api_gateway_requests(),
        'dynamodb_usage': get_dynamodb_usage()
    }

def check_thresholds():
    usage = get_monthly_usage()

    if usage['s3_storage_gb'] > 4.5:  # 90% of free tier
        send_alert("S3 storage approaching free tier limit")
```

---

#### **8. Cold Start Latency**

**Challenge:**
- Lambda cold starts (200-500ms for Python)
- User-facing API slowdown
- Poor user experience

**Mitigation:**
1. **Lambda SnapStart:** Enable for Python functions (new in 2024)
2. **Provisioned Concurrency:** Keep 1 instance warm (costs money - NOT recommended for MVP)
3. **Optimize Package Size:** Reduce dependencies
4. **ARM64 Architecture:** Faster cold starts
5. **User Expectations:** First request may be slow (acceptable for MVP)

**SnapStart Configuration:**
```yaml
Function:
  Type: AWS::Serverless::Function
  Properties:
    SnapStart:
      ApplyOn: PublishedVersions
```

---

## Alternative Architectural Approaches

### Alternative 1: Monolithic Backend (Not Recommended)

**Architecture:**
- Single EC2 instance running FastAPI
- PostgreSQL RDS database
- Traditional server-based deployment

**Pros:**
- Simpler local development
- Familiar architecture
- Easier debugging

**Cons:**
- **Costs:** EC2 + RDS = ~$15-30/month (exceeds free tier)
- Manual scaling
- Server management overhead
- No auto-scaling
- Less fault-tolerant

**Verdict:** ❌ Not recommended (cost + complexity)

---

### Alternative 2: Serverless Framework Instead of SAM

**Architecture:**
- Use Serverless Framework instead of AWS SAM
- Same AWS services

**Pros:**
- More mature ecosystem
- Better plugin support
- Multi-cloud support (if needed later)
- Larger community

**Cons:**
- Third-party dependency
- Less AWS-native than SAM
- Slightly more complex configuration

**Verdict:** ⚠️ Viable alternative, but SAM is simpler for AWS-only

**When to Choose Serverless Framework:**
- If you need multi-cloud support later
- If you prefer richer plugin ecosystem
- If you're already familiar with it

---

### Alternative 3: Next.js Full-Stack (Not Recommended for MVP)

**Architecture:**
- Next.js for both frontend and backend (API routes)
- Deploy to Vercel (free tier) or AWS Amplify
- PostgreSQL via Vercel Postgres or Neon

**Pros:**
- Single codebase (TypeScript)
- API routes co-located with frontend
- Excellent developer experience
- Fast iteration

**Cons:**
- **Vendor Lock-in:** Vercel-specific features
- **AWS Deployment:** Complex serverless Next.js on AWS
- **Costs:** Vercel Pro ($20/month) for production features
- **Python Requirement:** Can't use Python for backend
- Overkill for single-user app

**Verdict:** ❌ Not recommended (mission requires Python + AWS)

---

### Alternative 4: Use Unified Social Media API Service

**Architecture:**
- Use third-party service (Ayrshare, Buffer, Hootsuite API)
- Simplified backend (just proxy to service)
- Thin wrapper around paid API

**Pros:**
- **Rapid Development:** 10x faster implementation
- **Maintained APIs:** Service handles platform changes
- **Unified Interface:** Single API for all platforms
- **Webhooks:** Real-time comment notifications

**Cons:**
- **COST:** $20-50/month minimum (Ayrshare)
- **Dependency:** Reliance on third-party service
- **Less Control:** Limited customization
- **Vendor Lock-in:** Hard to migrate off

**Example Services:**
- **Ayrshare:** $20/month (5 platforms, 500 posts/month)
- **Buffer API:** $50/month (10 profiles)
- **Hootsuite API:** Enterprise pricing

**Verdict:** ⚠️ Consider for Phase 2 if direct integration becomes too complex

**When to Choose:**
- Budget allows $20-50/month
- Speed to market is critical
- Limited development resources

---

### Alternative 5: Hybrid Approach (Recommended for Future)

**Architecture:**
- MVP: Direct platform integrations (free)
- Phase 2: Evaluate unified API service
- Keep option to switch

**Benefits:**
- Start free, add paid service if needed
- Validate product-market fit before committing to costs
- Learn platform APIs deeply

**Implementation:**
```python
# Abstract interface allows switching
class PlatformService:
    async def post(self, content):
        pass

class DirectFacebookService(PlatformService):
    """Direct Facebook Graph API integration"""
    async def post(self, content):
        # Direct API call
        pass

class AyrshareService(PlatformService):
    """Unified API via Ayrshare"""
    async def post(self, content):
        # Call Ayrshare API
        pass

# Easily swap implementations
def get_platform_service(platform):
    if USE_UNIFIED_API:
        return AyrshareService()
    else:
        return DirectFacebookService()
```

---

## Conclusion & Recommendations

### Recommended Architecture Summary

**Backend:**
- ✅ FastAPI + AWS Lambda (Python 3.12, ARM64)
- ✅ API Gateway (HTTP API)
- ✅ DynamoDB (single-table design, on-demand)
- ✅ S3 + CloudFront (media + frontend hosting)
- ✅ SQS (async job queue)
- ✅ Cognito (authentication)
- ✅ Secrets Manager OR SSM Parameter Store (secrets)
- ✅ EventBridge (scheduled tasks)
- ✅ AWS SAM (IaC)

**Frontend:**
- ✅ React + Vite (fast builds, small bundle)
- ✅ Zustand (state management)
- ✅ Shadcn/ui (UI components)
- ✅ React Query (server state)
- ✅ Deployed to S3/CloudFront

**Social Platforms (MVP):**
- ✅ Facebook (recommended)
- ✅ YouTube (recommended)
- ✅ Instagram (if business account setup is feasible)
- ❌ X/Twitter (too expensive for free tier)

**Cost Estimate:**
- First 12 months: ~$2-3/month
- After 12 months: ~$2.60/month
- **Annual cost (after free tier):** ~$31/year

### Next Steps

1. **User Decisions:**
   - Review "Technical Decisions Requiring Input" section
   - Confirm platform priorities
   - Decide on cost trade-offs (Secrets Manager, custom domain, etc.)

2. **Initial Setup (Week 1):**
   - Create AWS account
   - Set up GitHub repository
   - Initialize project structure using SAM
   - Create React app with Vite

3. **Development (Weeks 2-8):**
   - Follow implementation roadmap
   - Week-by-week milestones
   - Regular testing and iteration

4. **Launch (Week 8):**
   - Deploy MVP to production
   - Begin posting to social platforms
   - Gather feedback

5. **Phase 2 (Weeks 9-12):**
   - Add comment aggregation
   - Build comment dashboard
   - Implement reply functionality

### Success Metrics

**MVP Goals:**
- ✅ Zero cost (within AWS Free Tier)
- ✅ Single-user posting to 3+ platforms
- ✅ Video and image support
- ✅ <5 second post publishing time
- ✅ >99% posting success rate
- ✅ Mobile-responsive UI

**Phase 2 Goals:**
- ✅ Comment aggregation (<15 min delay)
- ✅ Reply to comments
- ✅ Email notifications
- ✅ Still within/near AWS Free Tier

---

## Appendix

### Useful Resources

**AWS Documentation:**
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [DynamoDB Single-Table Design](https://aws.amazon.com/blogs/database/single-table-vs-multi-table-design-in-amazon-dynamodb/)
- [API Gateway HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api.html)

**Social Media APIs:**
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [LinkedIn API](https://learn.microsoft.com/en-us/linkedin/)
- [TikTok API](https://developers.tiktok.com/)

**Frontend:**
- [Vite Documentation](https://vitejs.dev/)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/)
- [Shadcn/ui](https://ui.shadcn.com/)
- [React Query](https://tanstack.com/query/)

**Tools:**
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [AWS CLI](https://aws.amazon.com/cli/)
- [Postman](https://www.postman.com/) - API testing

### Glossary

- **API Gateway:** AWS service for creating REST/HTTP APIs
- **CloudFront:** AWS CDN (Content Delivery Network)
- **Cognito:** AWS authentication service
- **DynamoDB:** AWS NoSQL database
- **EventBridge:** AWS event bus for scheduled tasks
- **Lambda:** AWS serverless compute service
- **S3:** AWS object storage service
- **SAM:** AWS Serverless Application Model (IaC)
- **SQS:** AWS message queue service
- **OAuth 2.0:** Authorization framework for third-party access
- **JWT:** JSON Web Token (authentication token)
- **MAU:** Monthly Active Users (Cognito pricing metric)
- **WCU/RCU:** Write/Read Capacity Units (DynamoDB)

---

**End of Architecture Document**

*This architecture is designed to evolve with your ministry's needs while maintaining cost efficiency and scalability. May this platform effectively spread the gospel message to all creation!*
