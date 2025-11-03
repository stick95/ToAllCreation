# ToAllCreation

**Gospel-Focused Social Media Aggregator**

> *"Go into all the world and preach the gospel to all creation." - Mark 16:15*

---

## Overview

ToAllCreation is a serverless social media management platform designed to help spread the gospel message efficiently across multiple social media platforms. Built on AWS with a focus on cost-efficiency and scalability.

### Mission

Provide a free, accessible platform for gospel content creators to reach audiences across Facebook, Instagram, YouTube, and other social networks simultaneously.

### Key Features

- **Multi-Platform Posting:** Share content to Facebook, Instagram, and YouTube simultaneously
- **Media Support:** Upload and share images, videos, and short-form content (Reels, Shorts)
- **Comment Aggregation (Phase 2):** View and respond to comments from all platforms in one place
- **Cost-Effective:** Built to operate within AWS Free Tier ($2-3/month)
- **Serverless Architecture:** Auto-scaling, zero server management

---

## Quick Start

### Prerequisites

- AWS Account (Free Tier)
- Node.js 20+
- Python 3.12+
- AWS CLI
- AWS SAM CLI
- Git

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/toallcreation.git
cd toallcreation

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Deploy infrastructure
cd ../backend
sam build
sam deploy --guided

# Deploy frontend
cd ../frontend
npm run build
aws s3 sync dist/ s3://toallcreation-frontend
```

### Configuration

1. Create AWS account and configure credentials
2. Set up social media developer accounts:
   - Facebook Developer Account → Create App
   - Google Cloud Console → Enable YouTube Data API
   - Instagram Business Account → Link to Facebook Page
3. Configure environment variables (see `.env.example`)
4. Deploy using SAM CLI

---

## Architecture

### High-Level Components

```
┌─────────────┐
│   USER      │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────┐
│  CloudFront CDN                             │
│  ┌─────────────┐    ┌──────────────────┐   │
│  │  React SPA  │    │   API Gateway    │   │
│  │  (S3)       │    │   (HTTP API)     │   │
│  └─────────────┘    └─────────┬────────┘   │
└────────────────────────────────┼────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼──────┐         ┌───────▼────────┐
              │  Cognito   │         │  Lambda        │
              │  (Auth)    │         │  (FastAPI)     │
              └────────────┘         └────────┬───────┘
                                              │
                    ┌─────────────────────────┼──────────────┐
                    │                         │              │
              ┌─────▼──────┐         ┌────────▼─────┐  ┌────▼────┐
              │  DynamoDB  │         │     SQS      │  │   S3    │
              │  (Data)    │         │  (Queue)     │  │ (Media) │
              └────────────┘         └──────┬───────┘  └─────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
                                    │ Social Media  │
                                    │  Platforms    │
                                    │ • Facebook    │
                                    │ • Instagram   │
                                    │ • YouTube     │
                                    └───────────────┘
```

### Technology Stack

**Backend:**
- FastAPI (Python 3.12)
- AWS Lambda (ARM64)
- API Gateway (HTTP API)
- DynamoDB (Single-Table Design)
- SQS (Job Queue)
- Secrets Manager (API Tokens)

**Frontend:**
- React 18
- Vite (Build Tool)
- Zustand (State Management)
- Shadcn/ui (Components)
- TailwindCSS

**Infrastructure:**
- AWS SAM (Infrastructure as Code)
- GitHub Actions (CI/CD)
- CloudFront (CDN)
- Cognito (Authentication)

**Social Media APIs:**
- Facebook Graph API
- Instagram Graph API
- YouTube Data API v3
- LinkedIn API (future)
- TikTok Content API (future)

---

## Project Structure

```
toallcreation/
├── backend/                    # Python backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Core business logic
│   │   ├── models/            # Pydantic models
│   │   ├── services/          # External integrations
│   │   └── workers/           # Background workers
│   ├── tests/                 # Backend tests
│   ├── template.yaml          # SAM template
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/             # Page components
│   │   ├── store/             # Zustand stores
│   │   ├── api/               # API client
│   │   └── hooks/             # Custom hooks
│   ├── public/
│   └── package.json
│
├── .github/
│   └── workflows/             # GitHub Actions
│       └── deploy.yml
│
├── docs/                      # Documentation
│   ├── API.md                # API documentation
│   ├── DEPLOYMENT.md         # Deployment guide
│   └── DEVELOPMENT.md        # Development guide
│
├── ARCHITECTURE.md           # Comprehensive architecture
├── README.md                 # This file
└── LICENSE
```

---

## Features

### MVP (Phase 1)

- [x] User authentication (AWS Cognito)
- [x] Connect social media accounts (OAuth)
- [x] Post text content to multiple platforms
- [x] Upload and share images
- [x] Upload and share videos
- [x] Platform-specific content (Reels, Shorts)
- [x] Post status tracking
- [x] Error handling and retry logic

### Phase 2 (In Progress)

- [ ] Aggregate comments from all platforms
- [ ] Reply to comments within app
- [ ] Real-time comment notifications
- [ ] Comment filtering and search

### Future Enhancements

- [ ] Scheduled posting
- [ ] Analytics dashboard
- [ ] Content calendar
- [ ] Multi-user support
- [ ] Donation system integration
- [ ] iOS/Android mobile apps (Flutter)
- [ ] AI-powered content suggestions
- [ ] Hashtag recommendations

---

## Deployment

### AWS Free Tier Costs

**First 12 Months:**
- Lambda: FREE (1M requests/month)
- API Gateway: FREE (1M requests/month)
- DynamoDB: FREE (25 GB, 25 RCU/WCU)
- S3: FREE (5 GB storage)
- CloudFront: FREE (1 TB transfer, 10M requests)
- Cognito: FREE (50K MAU)
- **Estimated Cost:** ~$2-3/month (Secrets Manager only)

**After 12 Months:**
- Most services remain in permanent free tier
- **Estimated Cost:** ~$2.60/month

### Deployment Steps

```bash
# 1. Configure AWS credentials
aws configure

# 2. Deploy backend
cd backend
sam build --use-container
sam deploy --guided

# 3. Deploy frontend
cd ../frontend
npm run build
aws s3 sync dist/ s3://toallcreation-frontend --delete
aws cloudfront create-invalidation --distribution-id XXXXX --paths "/*"
```

---

## Development

### Local Development

```bash
# Backend
cd backend
pip install -r requirements-dev.txt
sam local start-api

# Frontend
cd frontend
npm run dev
```

### Testing

```bash
# Backend tests
cd backend
pytest tests/ --cov=app

# Frontend tests
cd frontend
npm test
```

### Environment Variables

Create `.env` files:

**Backend (.env):**
```
AWS_REGION=us-east-1
TABLE_NAME=ToAllCreation
BUCKET_NAME=toallcreation-media
QUEUE_URL=https://sqs.us-east-1.amazonaws.com/...
```

**Frontend (.env.local):**
```
VITE_API_URL=https://api.toallcreation.com
VITE_COGNITO_USER_POOL_ID=us-east-1_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
```

---

## API Documentation

See [API.md](docs/API.md) for full API documentation.

### Key Endpoints

```
POST   /api/v1/auth/login
GET    /api/v1/platforms
POST   /api/v1/platforms/{platform}/connect
GET    /api/v1/posts
POST   /api/v1/posts
POST   /api/v1/posts/{id}/publish
GET    /api/v1/comments
POST   /api/v1/comments/{id}/reply
```

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Write tests for new features
- Follow PEP 8 (Python) and ESLint (TypeScript)
- Update documentation
- Ensure CI/CD passes

---

## Security

- All secrets stored in AWS Secrets Manager (encrypted)
- HTTPS enforced (CloudFront + API Gateway)
- JWT authentication via Cognito
- Input validation with Pydantic
- IAM roles follow least-privilege principle

**Report security vulnerabilities:** security@toallcreation.com

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

For questions or support:

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/toallcreation/issues)
- Email: support@toallcreation.com

---

## Acknowledgments

- Built with AWS Free Tier
- Powered by FastAPI and React
- Social media integrations via platform APIs
- Inspired by the Great Commission (Mark 16:15)

---

**Spread the Gospel. Reach All Creation.**
