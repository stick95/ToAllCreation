# ToAllCreation

> "Go into all the world and preach the gospel to all creation." - Mark 16:15

A comprehensive social media cross-posting application that enables users to share content simultaneously across multiple platforms with scheduling capabilities and async processing.

## Features

### Core Functionality
- **Multi-Platform Posting**: Share content to Facebook, Instagram, Twitter, YouTube, LinkedIn, and TikTok from a single interface
- **Scheduled Posts**: Schedule content for future publication with automatic processing
- **Async Upload Processing**: Background processing of media uploads via AWS SQS for improved performance
- **Social Media Account Management**: Connect and manage multiple social media accounts per platform
- **Media Library**: Upload and organize images, videos, and other media files in S3

### Authentication & Security
- **AWS Cognito Integration**: Secure user authentication and authorization
- **Password Reset Flow**: Self-service password reset with email verification
- **Protected Routes**: Client-side route protection for authenticated users
- **Security Audited**: Comprehensive security review completed (see docs/AUTH-SECURITY-AUDIT.md)

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast builds and HMR
- **React Router** for client-side routing
- **Zustand** for state management
- **Axios** for API communication

### Backend
- **FastAPI** Python web framework
- **AWS Lambda** with SAM (Serverless Application Model)
- **AWS API Gateway** for REST API
- **AWS Cognito** for authentication
- **DynamoDB** for data persistence
- **S3** for media storage
- **SQS** for async job processing
- **CloudFront** for CDN

## Project Structure

```
ToAllCreation/
├── frontend/               # React + TypeScript + Vite application
│   ├── src/
│   │   ├── assets/        # Images and static assets
│   │   ├── components/    # React components (auth, layout, etc.)
│   │   ├── pages/         # Page components (Dashboard, Accounts, etc.)
│   │   ├── stores/        # Zustand state stores
│   │   └── App.tsx        # Main app component with routing
│   └── dist/              # Production build output
├── backend/               # FastAPI Lambda functions
│   ├── api/               # API Lambda function
│   ├── worker/            # Background worker Lambda
│   └── lib/               # Shared libraries (auth, database, social)
├── docs/                  # Comprehensive documentation
└── template.yaml          # AWS SAM template
```

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- AWS CLI configured with appropriate credentials
- AWS SAM CLI

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Backend Development

```bash
# Build and deploy
export AWS_PROFILE=ToAllCreation
sam build
sam deploy
```

### Environment Variables

See `docs/GITHUB-SECRETS-SETUP.md` for required environment variables including:
- AWS credentials
- Cognito configuration
- Social media API credentials
- Database table names
- S3 bucket names

## Documentation

Comprehensive documentation is available in the `/docs` directory:

### Architecture & Design
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Complete system architecture (3,400+ lines)
- **[DESIGN-SYSTEM.md](docs/DESIGN-SYSTEM.md)** - UI/UX design system and components
- **[SOCIAL-MEDIA-POSTING.md](docs/SOCIAL-MEDIA-POSTING.md)** - Posting architecture and database schema

### Authentication
- **[AUTH-ARCHITECTURE.md](docs/AUTH-ARCHITECTURE.md)** - Authentication system design
- **[AUTH-SECURITY-AUDIT.md](docs/AUTH-SECURITY-AUDIT.md)** - Security audit and OWASP analysis
- **[AUTH-TESTING.md](docs/AUTH-TESTING.md)** - Authentication testing guide

### Platform Integration
- **[TWITTER_INTEGRATION.md](docs/TWITTER_INTEGRATION.md)** - Twitter/X API integration guide

### Deployment
- **[UNIFIED-DEPLOYMENT.md](docs/UNIFIED-DEPLOYMENT.md)** - Deployment strategy and workflow
- **[AWS_SERVICES_GUIDE.md](docs/AWS_SERVICES_GUIDE.md)** - AWS services configuration
- **[CLOUDFRONT-INFO.md](docs/CLOUDFRONT-INFO.md)** - CloudFront CDN setup

### Reference
- **[INDEX.md](docs/INDEX.md)** - Documentation index and quick reference
- **[TECHNICAL_DECISIONS.md](docs/TECHNICAL_DECISIONS.md)** - Key technical decisions

## API Endpoints

The backend provides RESTful endpoints for:

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/confirm-password` - Confirm password reset with code
- `GET /api/auth/me` - Get current user info

### Social Media Accounts
- `GET /api/accounts` - List connected accounts
- `POST /api/accounts` - Connect new social media account
- `PUT /api/accounts/{account_id}` - Update account
- `DELETE /api/accounts/{account_id}` - Disconnect account

### Media Management
- `GET /api/uploads` - List uploaded media
- `POST /api/uploads` - Upload new media file
- `DELETE /api/uploads/{upload_id}` - Delete media

### Post Management
- `POST /api/posts` - Create and publish/schedule post
- `GET /api/posts/scheduled` - List scheduled posts
- `PUT /api/posts/{post_id}` - Update scheduled post
- `DELETE /api/posts/{post_id}` - Delete scheduled post
- `POST /api/posts/{post_id}/resubmit` - Retry failed post

### System
- `GET /health` - Health check
- `GET /` - Root endpoint

## Database Schema

### Tables
- **users** - User accounts and profiles
- **social_accounts** - Connected social media accounts
- **uploads** - Media files in S3
- **posts** - Published and scheduled posts
- **post_platforms** - Post status per platform

See `docs/SOCIAL-MEDIA-POSTING.md` for detailed schema.

## Async Processing

The application uses AWS SQS for background processing:

1. User uploads media → Immediate response with upload ID
2. Media is queued for processing
3. Worker Lambda processes upload asynchronously
4. Status updates stored in DynamoDB

## Deployment

The application is deployed using AWS SAM:

- **Frontend**: CloudFront + S3
- **Backend**: API Gateway + Lambda
- **Region**: us-west-2

See `docs/UNIFIED-DEPLOYMENT.md` for deployment procedures.

## License

[To be specified]

## Support

For issues and questions, please refer to the documentation in the `/docs` directory or create an issue in the repository.

---

**Built with purpose**: Empowering users to share their message across all digital platforms.
