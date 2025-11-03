# Technical Decisions Required - ToAllCreation

This document outlines key technical decisions that need to be made before beginning implementation. Please review each section and make your selections.

---

## 1. Social Media Platform Priority

### Question
Which platforms are MUST-HAVE for the MVP launch?

### Options

#### Tier 1: RECOMMENDED (Free, Reliable APIs)
- [ ] **Facebook** - Most mature API, easiest integration, real-time webhooks
- [ ] **YouTube** - Essential for video ministry, good API, manageable quotas
- [ ] **Instagram** - Large reach, but requires Business account setup

#### Tier 2: OPTIONAL (Good APIs, but lower priority)
- [ ] **LinkedIn** - Professional audience, requires API approval
- [ ] **TikTok** - Short-form video, newer API, limited features

#### Tier 3: NOT RECOMMENDED (Cost prohibitive)
- [ ] **X/Twitter** - Requires paid tier ($100-200/month minimum)

### My Decision
```
MVP Platforms:
1. [ ] Facebook
2. [ ] YouTube
3. [ ] Instagram
4. [ ] LinkedIn (Phase 2)
5. [ ] TikTok (Phase 2)
6. [ ] X/Twitter (Yes/No - requires budget)

Notes:
_________________________________________
_________________________________________
```

### Instagram Business Account Setup
If Instagram is selected:
- [ ] I have or can create a Facebook Page for the ministry
- [ ] I have or can convert Instagram to Business account
- [ ] I understand business verification may be required
- [ ] I have admin access to both accounts

---

## 2. Video Storage & Compression Strategy

### Question
How should we handle video storage to stay within 5 GB S3 free tier?

### Background
- S3 Free Tier: 5 GB storage
- Typical video size: 50-500 MB (uncompressed)
- Risk: 10-20 videos could exceed free tier

### Options

#### Option A: Client-Side Compression (Low Cost, Moderate Quality)
- Compress videos in browser before upload
- User waits during compression
- **Cost:** $0
- **Quality:** Moderate (browser limitations)

#### Option B: Server-Side Optimization (Better Quality, Higher Cost)
- Upload original, Lambda optimizes with FFmpeg
- Transparent to user
- **Cost:** ~$1-2/month (Lambda execution time)
- **Quality:** High (professional-grade compression)

#### Option C: Lifecycle Policies + Compression (Balanced)
- Compress videos (client or server)
- Delete videos after 90 days automatically
- Move to cheaper storage (S3-IA) after 30 days
- **Cost:** $0-1/month
- **Trade-off:** Videos deleted after 90 days

#### Option D: External Video Hosting (Zero S3 Cost)
- Store videos on YouTube/Vimeo long-term
- S3 only for temporary processing
- **Cost:** $0
- **Trade-off:** Dependency on third-party

### My Decision
```
Selected Option: [ A / B / C / D ]

Video Retention Policy:
- Keep videos for: [ 30 / 60 / 90 / Forever ] days

Maximum Video Size:
- File size limit: [ 50 MB / 100 MB / 500 MB / Unlimited ]
- Resolution limit: [ 720p / 1080p / 4K ]

Compression Quality:
- [ ] Maximum compression (smallest file)
- [ ] Balanced (recommended)
- [ ] Minimal compression (best quality)

Notes:
_________________________________________
_________________________________________
```

---

## 3. Secrets Management Strategy

### Question
Should we use AWS Secrets Manager or AWS Systems Manager Parameter Store?

### Comparison

| Feature | Secrets Manager | SSM Parameter Store |
|---------|-----------------|---------------------|
| **Cost** | $0.40/secret/month | FREE (Standard tier) |
| **Annual Cost (5 secrets)** | ~$24/year | $0 |
| **Automatic Rotation** | Yes | No (manual) |
| **Encryption** | Yes (KMS) | Yes (KMS) |
| **Versioning** | Yes | Yes |

### Options

#### Option A: Secrets Manager (Automated, Costs Money)
- **Pros:** Automatic token rotation, managed service
- **Cons:** ~$24/year for 5 platform secrets
- **Best For:** Production apps requiring high security

#### Option B: SSM Parameter Store (Free, Manual)
- **Pros:** Completely free, encrypted
- **Cons:** Manual token rotation every 60 days
- **Best For:** MVP, cost-conscious deployments

#### Option C: Hybrid (Balanced)
- Use SSM for static secrets (app IDs, client secrets)
- Use Secrets Manager only for auto-rotating tokens
- **Cost:** ~$8-12/year
- **Best For:** Balanced security and cost

### My Decision
```
Selected Option: [ A / B / C ]

Token Rotation Strategy:
- [ ] Automatic (requires Secrets Manager)
- [ ] Manual every 60 days (calendar reminder)
- [ ] Manual on-demand (when expired)

Budget Allocation:
- Willing to spend $24/year for automation: [ Yes / No ]

Notes:
_________________________________________
_________________________________________
```

---

## 4. Custom Domain Setup

### Question
Should we use a custom domain or AWS-provided URLs?

### Options

#### Option A: Custom Domain (Professional)
- Domain: `toallcreation.com` or similar
- **Cost:** ~$12/year (domain) + $6/year (Route 53) = $18/year
- **Pros:** Professional branding, memorable URLs
- **Cons:** Additional setup, annual cost
- **URLs:**
  - Frontend: `https://app.toallcreation.com`
  - API: `https://api.toallcreation.com`

#### Option B: AWS-Provided URLs (Free)
- **Cost:** $0
- **Pros:** Zero cost, zero config
- **Cons:** Ugly URLs, less professional
- **URLs:**
  - Frontend: `https://d1a2b3c4d5e6f7.cloudfront.net`
  - API: `https://abc123xyz.execute-api.us-east-1.amazonaws.com`

### My Decision
```
Selected Option: [ A / B ]

If Custom Domain:
- Preferred domain name: _________________________
- Already own domain: [ Yes / No ]
- Budget approved ($18/year): [ Yes / No ]

Launch Strategy:
- [ ] Start with AWS URLs, add custom domain later
- [ ] Custom domain from day 1

Notes:
_________________________________________
_________________________________________
```

---

## 5. Email Service Configuration

### Question
Which email service should Cognito use for auth emails?

### Background
Cognito needs to send emails for:
- Password reset
- Email verification
- MFA (if enabled)
- Account notifications

### Options

#### Option A: Cognito Email Service (Simple)
- **Free Tier:** 50 emails/day
- **Cost:** Included in Cognito
- **Pros:** Zero config
- **Cons:** 50 email/day limit
- **Best For:** Single user MVP

#### Option B: Amazon SES (Scalable)
- **Free Tier:** 62,000 emails/month (from EC2/Lambda)
- **Cost:** $0.10 per 1,000 emails after free tier
- **Pros:** Higher limits, professional sender
- **Cons:** Domain verification required
- **Best For:** Multi-user, production

### My Decision
```
Selected Option: [ A / B ]

Expected Email Volume:
- Estimated emails per day: [ <10 / 10-50 / 50+ ]

If SES Selected:
- Domain for sending emails: _________________________
- Have access to domain DNS: [ Yes / No ]

Launch Strategy:
- [ ] Start with Cognito Email, migrate to SES later
- [ ] Set up SES from day 1

Notes:
_________________________________________
_________________________________________
```

---

## 6. Development Environment Strategy

### Question
How should we set up the local development environment?

### Options

#### Option A: Direct AWS Development Stack (RECOMMENDED)
- Create separate AWS dev environment
- Deploy to real AWS services
- **Pros:** 100% production parity, simple
- **Cons:** Requires AWS account
- **Cost:** Within free tier (~$0-1/month)

#### Option B: LocalStack (Community Edition)
- Emulate AWS services locally
- **Pros:** No AWS costs during development
- **Cons:** Not 100% compatible, setup complexity
- **Cost:** $0 (Community), $45/month (Pro)

#### Option C: AWS SAM Local + Hybrid
- Run Lambda functions locally
- Connect to real AWS for DynamoDB, S3
- **Pros:** Partial local development
- **Cons:** Requires AWS account for some services

### My Decision
```
Selected Option: [ A / B / C ]

Development AWS Account:
- [ ] Use separate AWS account for dev
- [ ] Use same AWS account (different stack name)

Local Testing Preference:
- [ ] Full cloud-based development
- [ ] Hybrid (local Lambda, cloud services)
- [ ] Fully local (LocalStack)

Notes:
_________________________________________
_________________________________________
```

---

## 7. Monitoring & Alerting Setup

### Question
What level of monitoring and alerting do we need?

### Options

#### Option A: Basic CloudWatch Logs (Free)
- Lambda function logs
- Manual review only
- **Cost:** $0
- **Best For:** MVP, manual monitoring

#### Option B: CloudWatch Alarms + Email Alerts (Recommended)
- Automated alerts via email (SNS)
- Monitor errors, throttling, costs
- **Cost:** ~$0.50/month
- **Best For:** Production monitoring

#### Option C: Third-Party Monitoring (Advanced)
- Datadog, New Relic, Sentry
- Advanced dashboards and alerting
- **Cost:** $15-50/month
- **Best For:** Enterprise production

### My Decision
```
Selected Option: [ A / B / C ]

Alerts Configuration:
Email for alerts: _________________________

Critical Events to Monitor:
- [ ] Failed authentication attempts
- [ ] API errors (5xx responses)
- [ ] DynamoDB throttling
- [ ] S3 storage approaching 5 GB
- [ ] Lambda errors
- [ ] Cost exceeding $5/month

Alert Frequency:
- [ ] Immediate (real-time)
- [ ] Daily digest
- [ ] Weekly summary

Notes:
_________________________________________
_________________________________________
```

---

## 8. Testing Strategy & Coverage

### Question
What level of test coverage should we target?

### Options

#### Option A: Minimal Testing (Critical Paths Only)
- Test only authentication and posting
- **Coverage:** ~30-40%
- **Pros:** Fast development
- **Cons:** Higher bug risk

#### Option B: Moderate Testing (RECOMMENDED)
- Test core functionality and integrations
- **Coverage:** ~70% backend, ~50% frontend
- **Pros:** Balance speed and reliability
- **Cons:** Some development overhead

#### Option C: Comprehensive Testing
- Full unit, integration, and E2E tests
- **Coverage:** ~90% backend, ~80% frontend
- **Pros:** Very reliable, production-grade
- **Cons:** Significant development time

### My Decision
```
Selected Option: [ A / B / C ]

Testing Priorities:
- [ ] Unit tests (functions, components)
- [ ] Integration tests (API endpoints)
- [ ] E2E tests (full user workflows)
- [ ] Manual testing only

CI/CD Requirements:
- [ ] All tests must pass before merge
- [ ] Tests optional (manual review)
- [ ] No automated testing

Test Environments:
- [ ] Development environment for testing
- [ ] Staging environment before production
- [ ] Direct to production (YOLO mode)

Notes:
_________________________________________
_________________________________________
```

---

## 9. Rate Limiting & Posting Strategy

### Question
How should we handle rate limits across platforms?

### Background
Different platforms have different rate limits:
- Facebook: ~200 posts/hour
- Instagram: 25 posts/day
- YouTube: 6-20 uploads/day
- TikTok: 30 posts/day

### Options

#### Option A: Sequential Posting (Safe)
- Post to platforms one at a time
- 2-second delay between platforms
- **Pros:** No rate limit issues
- **Cons:** Slower (6-10 seconds per post)

#### Option B: Parallel Posting (Fast)
- Post to all platforms simultaneously
- **Pros:** Fast (2-3 seconds total)
- **Cons:** May trigger rate limits

#### Option C: Smart Queuing (Balanced)
- Queue posts, process based on platform limits
- Retry with exponential backoff
- **Pros:** Optimal speed, handles errors
- **Cons:** More complex

### My Decision
```
Selected Option: [ A / B / C ]

Posting Volume Expectations:
- Posts per day: [ 1-5 / 5-10 / 10-20 / 20+ ]
- Peak posting hours: [ Morning / Afternoon / Evening / All day ]

Error Handling:
- [ ] Retry failed posts automatically (3 attempts)
- [ ] Notify user immediately on failure
- [ ] Daily error summary

User Experience Priority:
- [ ] Speed (parallel posting)
- [ ] Reliability (sequential posting)
- [ ] Balanced (smart queuing)

Notes:
_________________________________________
_________________________________________
```

---

## 10. Database Design Validation

### Question
Confirm database design approach

### Options

#### Option A: Single-Table Design (RECOMMENDED)
- One DynamoDB table for all entities
- **Pros:** Cost-efficient, performant, scalable
- **Cons:** Complex access patterns
- **Free Tier:** Efficient use of 25 RCU/WCU

#### Option B: Multi-Table Design
- Separate tables for Users, Posts, Comments, etc.
- **Pros:** Simpler queries, clear separation
- **Cons:** May exceed free tier capacity limits
- **Free Tier:** Splits 25 RCU/WCU across tables

### My Decision
```
Selected Option: [ A / B ]

Data Retention:
- Posts: Keep for [ 90 days / 1 year / Forever ]
- Comments: Keep for [ 90 days / 1 year / Forever ]
- Media: Keep for [ 30 / 60 / 90 days ]

Backup Strategy:
- [ ] Enable DynamoDB Point-in-Time Recovery ($$$)
- [ ] Manual exports periodically (free)
- [ ] No backups (risky)

Notes:
_________________________________________
_________________________________________
```

---

## Summary & Sign-Off

### Selected Configuration Summary

```
1. MVP Platforms: ______________________________
2. Video Strategy: ______________________________
3. Secrets Management: __________________________
4. Custom Domain: _______________________________
5. Email Service: _______________________________
6. Dev Environment: _____________________________
7. Monitoring Level: ____________________________
8. Test Coverage: _______________________________
9. Posting Strategy: ____________________________
10. Database Design: ____________________________
```

### Budget Summary

```
Estimated Monthly Costs:

First 12 Months:
- AWS Services: $____________
- Domain (if selected): $____________
- Third-party services: $____________
Total: $____________ /month

After 12 Months:
- AWS Services: $____________
- Domain (if selected): $____________
- Third-party services: $____________
Total: $____________ /month

Annual Budget: $____________
```

### Timeline Preferences

```
MVP Launch Target: ______________ (date)

Development Phases:
- Phase 1 (MVP): ______ weeks
- Phase 2 (Comments): ______ weeks
- Phase 3 (Future): ______ weeks

Team Size:
- Developers: ______
- Part-time / Full-time: __________
```

### Approval

```
Reviewed by: ____________________________
Date: ____________________________
Approved: [ Yes / Needs Revision ]

Revision Notes:
_________________________________________
_________________________________________
_________________________________________
```

---

## Next Steps

Once all decisions are made:

1. [ ] Review architecture document
2. [ ] Finalize technical decisions
3. [ ] Set up AWS account
4. [ ] Configure social media developer accounts
5. [ ] Initialize project repository
6. [ ] Begin Week 1 development tasks

**Ready to build? Let's spread the gospel to all creation!**
