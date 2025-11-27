# ToAllCreation - Documentation Index

**Complete documentation for the ToAllCreation social media cross-posting platform**

---

## Quick Navigation

### 🚀 Getting Started

Start here if you're new to the project:

1. **[README.md](../README.md)** - Project overview (root directory)
   - Feature list
   - Technology stack
   - Getting started guide
   - API endpoints overview
   - Database schema

2. **[DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md)** - UI/UX design system
   - Color palette
   - Typography
   - Component styles
   - Layout system

---

### 🏗️ Architecture & Design

Deep dive into technical architecture:

3. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Comprehensive architecture (3,400+ lines)
   - System architecture overview
   - Social media platform analysis
   - Technology stack recommendations
   - AWS infrastructure design
   - Backend architecture
   - Frontend architecture
   - Security & authentication
   - CI/CD pipeline
   - Cost analysis & free tier strategy
   - Implementation roadmap
   - Technical challenges & solutions
   - Alternative architectural approaches

**🎯 Core Reference:** Most comprehensive technical document.

4. **[SOCIAL-MEDIA-POSTING.md](./SOCIAL-MEDIA-POSTING.md)** - Posting system architecture
   - Database schema (users, social_accounts, posts, post_platforms, uploads)
   - Async processing workflow
   - Platform-specific posting logic
   - Status tracking and error handling
   - Scheduled posts implementation

---

### 🔐 Authentication & Security

Complete authentication system documentation:

5. **[AUTH-ARCHITECTURE.md](./AUTH-ARCHITECTURE.md)** - Authentication system design
   - AWS Cognito integration
   - User registration and login flows
   - Token management
   - Password reset workflow
   - Protected routes

6. **[AUTH-SECURITY-AUDIT.md](./AUTH-SECURITY-AUDIT.md)** - Security audit and OWASP analysis
   - Security assessment
   - Vulnerability analysis
   - OWASP Top 10 compliance
   - Security recommendations
   - Best practices

7. **[AUTH-TESTING.md](./AUTH-TESTING.md)** - Authentication testing guide
   - Test scenarios
   - Manual testing procedures
   - Automated testing strategies
   - Security testing

---

### 🌐 Platform Integration

Platform-specific integration guides:

8. **[TWITTER_INTEGRATION.md](./TWITTER_INTEGRATION.md)** - Twitter/X API integration
   - OAuth 2.0 authentication
   - Posting tweets with media
   - Error handling
   - Rate limiting
   - Testing procedures

---

### 🚀 Deployment & Infrastructure

Deployment and AWS infrastructure documentation:

9. **[UNIFIED-DEPLOYMENT.md](./UNIFIED-DEPLOYMENT.md)** - Deployment strategy
   - CI/CD workflow
   - GitHub Actions setup
   - Deployment procedures
   - Rollback strategies

10. **[AWS_SERVICES_GUIDE.md](./AWS_SERVICES_GUIDE.md)** - AWS services configuration
    - Lambda (serverless compute)
    - API Gateway (HTTP API)
    - DynamoDB (NoSQL database)
    - S3 (object storage)
    - CloudFront (CDN)
    - Cognito (authentication)
    - SQS (message queue)
    - Secrets Manager (credential storage)
    - CloudWatch (monitoring)
    - Configuration best practices

11. **[AWS-DEPLOYMENT-INFO.md](./AWS-DEPLOYMENT-INFO.md)** - AWS resources details
    - Deployed resources inventory
    - Resource ARNs and IDs
    - Configuration details

12. **[CLOUDFRONT-INFO.md](./CLOUDFRONT-INFO.md)** - CloudFront CDN configuration
    - Distribution setup
    - Cache behavior
    - SSL/TLS configuration
    - Performance optimization

13. **[GITHUB-SECRETS-SETUP.md](./GITHUB-SECRETS-SETUP.md)** - CI/CD secrets configuration
    - Required GitHub secrets
    - Environment variables
    - AWS credentials setup

---

### 📋 Reference Documents

14. **[TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md)** - Key technical decisions
    - Platform selection rationale
    - Technology choices
    - Architecture decisions
    - Trade-offs and considerations

---

## Documentation Overview

### Current Documentation Files

| Document | Purpose | Status |
|----------|---------|--------|
| [README.md](../README.md) | Project introduction, quick start | ✅ Current |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Complete technical architecture | ✅ Current |
| [SOCIAL-MEDIA-POSTING.md](./SOCIAL-MEDIA-POSTING.md) | Posting system and database | ✅ Current |
| [AUTH-ARCHITECTURE.md](./AUTH-ARCHITECTURE.md) | Authentication system | ✅ Current |
| [AUTH-SECURITY-AUDIT.md](./AUTH-SECURITY-AUDIT.md) | Security audit | ✅ Current |
| [AUTH-TESTING.md](./AUTH-TESTING.md) | Testing guide | ✅ Current |
| [TWITTER_INTEGRATION.md](./TWITTER_INTEGRATION.md) | Twitter integration | ✅ Current |
| [UNIFIED-DEPLOYMENT.md](./UNIFIED-DEPLOYMENT.md) | Deployment workflow | ✅ Current |
| [DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md) | UI/UX design | ✅ Current |
| [AWS_SERVICES_GUIDE.md](./AWS_SERVICES_GUIDE.md) | AWS services | 🔄 Needs update |
| [AWS-DEPLOYMENT-INFO.md](./AWS-DEPLOYMENT-INFO.md) | Resource inventory | 🔄 Needs update |
| [CLOUDFRONT-INFO.md](./CLOUDFRONT-INFO.md) | CDN configuration | 🔄 Needs update |
| [GITHUB-SECRETS-SETUP.md](./GITHUB-SECRETS-SETUP.md) | CI/CD secrets | 🔄 Needs update |
| [TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md) | Technical decisions | 🔄 Needs update |

---

## Recommended Reading Order

### For New Developers

Start with these documents to understand the project:

1. **[README.md](../README.md)** - Project overview
   - Understand features and capabilities
   - Review tech stack
   - See API endpoints

2. **[DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md)** - UI/UX design
   - Understand the visual design
   - Component library

3. **[AUTH-ARCHITECTURE.md](./AUTH-ARCHITECTURE.md)** - Authentication
   - How user authentication works
   - Cognito integration

4. **[SOCIAL-MEDIA-POSTING.md](./SOCIAL-MEDIA-POSTING.md)** - Posting system
   - Database schema
   - How posting works
   - Async processing

5. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Complete architecture
   - Deep dive into system design
   - Reference as needed

**Time Required:** ~2-3 hours

---

### For Deployment

Follow these for deploying the application:

1. **[AWS_SERVICES_GUIDE.md](./AWS_SERVICES_GUIDE.md)** - AWS setup
2. **[GITHUB-SECRETS-SETUP.md](./GITHUB-SECRETS-SETUP.md)** - Configure CI/CD
3. **[UNIFIED-DEPLOYMENT.md](./UNIFIED-DEPLOYMENT.md)** - Deploy the app

**Time Required:** ~1 hour reading + deployment time

---

### For Security Review

For security auditing and compliance:

1. **[AUTH-SECURITY-AUDIT.md](./AUTH-SECURITY-AUDIT.md)** - Security audit
2. **[AUTH-ARCHITECTURE.md](./AUTH-ARCHITECTURE.md)** - Auth implementation
3. **[AUTH-TESTING.md](./AUTH-TESTING.md)** - Security testing

**Time Required:** ~1-2 hours

---

## Key Features

### Implemented Features

- ✅ User authentication (AWS Cognito)
- ✅ Password reset with email verification
- ✅ Multi-platform posting (Facebook, Instagram, Twitter, YouTube, LinkedIn, TikTok)
- ✅ Social media account management
- ✅ Media upload and storage (S3)
- ✅ Async upload processing (SQS)
- ✅ Scheduled posts
- ✅ Post status tracking
- ✅ Error handling and retry logic

### Supported Platforms

- Facebook
- Instagram
- Twitter/X
- YouTube
- LinkedIn
- TikTok

---

## Technology Stack Summary

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite
- **Router:** React Router
- **State Management:** Zustand
- **HTTP Client:** Axios
- **Hosting:** S3 + CloudFront CDN

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Runtime:** AWS Lambda (ARM64)
- **API Gateway:** HTTP API
- **Database:** DynamoDB
- **Storage:** S3
- **Queue:** SQS
- **Auth:** AWS Cognito
- **Deployment:** AWS SAM

### Infrastructure
- **IaC:** AWS SAM
- **CI/CD:** GitHub Actions
- **Monitoring:** CloudWatch
- **CDN:** CloudFront
- **Region:** us-west-2

---

## Database Schema

### Core Tables
- **users** - User accounts and profiles
- **social_accounts** - Connected social media accounts
- **uploads** - Media files metadata
- **posts** - Published and scheduled posts
- **post_platforms** - Post status per platform

See [SOCIAL-MEDIA-POSTING.md](./SOCIAL-MEDIA-POSTING.md) for detailed schema.

---

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/confirm-password` - Confirm password reset
- `GET /api/auth/me` - Get current user

### Accounts
- `GET /api/accounts` - List connected accounts
- `POST /api/accounts` - Connect new account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Disconnect account

### Posts
- `POST /api/posts` - Create/schedule post
- `GET /api/posts/scheduled` - List scheduled posts
- `PUT /api/posts/{id}` - Update post
- `DELETE /api/posts/{id}` - Delete post
- `POST /api/posts/{id}/resubmit` - Retry failed post

### Uploads
- `GET /api/uploads` - List uploads
- `POST /api/uploads` - Upload media
- `DELETE /api/uploads/{id}` - Delete media

See [README.md](../README.md) for complete API documentation.

---

## Development Workflow

### Local Development

**Frontend:**
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

**Backend:**
```bash
export AWS_PROFILE=ToAllCreation
sam build
sam deploy
```

### Deployment

Push to `main` branch triggers automatic deployment via GitHub Actions.

See [UNIFIED-DEPLOYMENT.md](./UNIFIED-DEPLOYMENT.md) for details.

---

## Support & Resources

### Internal Documentation
- All documentation files in `/docs` directory
- Use this INDEX.md for navigation
- See individual files for specific topics

### External Resources
- [AWS Documentation](https://docs.aws.amazon.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [AWS SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)

### Social Media API Documentation
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api)
- [Twitter API](https://developer.twitter.com/en/docs)
- [YouTube API](https://developers.google.com/youtube/v3)
- [LinkedIn API](https://docs.microsoft.com/en-us/linkedin/)
- [TikTok API](https://developers.tiktok.com/)

---

## Mission

*"Go into all the world and preach the gospel to all creation." - Mark 16:15*

This platform empowers users to efficiently share their message across multiple social media platforms simultaneously, maximizing reach while minimizing effort.

---

**Ready to get started? Begin with [README.md](../README.md)!** 🚀
