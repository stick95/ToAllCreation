# ToAllCreation - Quick Start Guide

**Get up and running in under 30 minutes**

---

## What You'll Build

A serverless social media aggregator that allows you to:
- Post to Facebook, Instagram, and YouTube simultaneously
- Upload images and videos
- Track posting status per platform
- Aggregate and respond to comments (Phase 2)

**Cost:** ~$2-3/month within AWS Free Tier

---

## Prerequisites

Before starting, ensure you have:

### Required Accounts
- [ ] AWS Account ([sign up](https://aws.amazon.com))
- [ ] GitHub Account ([sign up](https://github.com))
- [ ] Facebook Developer Account ([create](https://developers.facebook.com))
- [ ] Google Cloud Account ([create](https://console.cloud.google.com))

### Required Software
- [ ] Node.js 20+ ([download](https://nodejs.org))
- [ ] Python 3.12+ ([download](https://python.org))
- [ ] Git ([download](https://git-scm.com))
- [ ] AWS CLI ([install](https://aws.amazon.com/cli))
- [ ] AWS SAM CLI ([install](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- [ ] Docker ([install](https://docker.com))

### Optional but Recommended
- [ ] VS Code ([download](https://code.visualstudio.com))
- [ ] Postman ([download](https://postman.com))

---

## Installation

### Step 1: Verify Prerequisites

```bash
# Verify installations
node --version    # Should be v20.x or higher
python --version  # Should be 3.12.x or higher
git --version
aws --version
sam --version
docker --version
```

### Step 2: Configure AWS

```bash
# Configure AWS credentials
aws configure

# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

### Step 3: Clone Repository

```bash
# Create project directory
mkdir toallcreation
cd toallcreation

# Initialize git
git init
```

---

## Backend Setup (10 minutes)

### 1. Initialize SAM Project

```bash
# Create backend
sam init

# Choose:
# - Template: AWS Quick Start Templates
# - Runtime: python3.12
# - Name: backend

# Enter backend directory
cd backend
```

### 2. Install Dependencies

```bash
# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
mangum==0.17.0
pydantic==2.5.0
boto3==1.29.7
httpx==0.25.2
python-jose[cryptography]==3.3.0
EOF

# Install
pip install -r requirements.txt
```

### 3. Deploy Infrastructure

```bash
# Build
sam build

# Deploy (guided first time)
sam deploy --guided

# Follow prompts:
# - Stack name: toallcreation-backend
# - Region: us-east-1
# - Confirm changes: Y
# - Allow IAM role creation: Y
# - Save arguments: Y
```

### 4. Note API URL

After deployment, note the API Gateway URL:
```
Outputs:
  ApiUrl: https://abc123xyz.execute-api.us-east-1.amazonaws.com/
```

---

## Frontend Setup (10 minutes)

### 1. Create React App

```bash
# Go back to project root
cd ..

# Create frontend with Vite
npm create vite@latest frontend -- --template react-ts

# Enter frontend directory
cd frontend
```

### 2. Install Dependencies

```bash
# Install core dependencies
npm install

# Install additional packages
npm install zustand react-router-dom @tanstack/react-query axios

# Install dev dependencies
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 3. Configure Environment

```bash
# Create .env.local
cat > .env.local << EOF
VITE_API_URL=<your-api-gateway-url>
VITE_COGNITO_USER_POOL_ID=<your-user-pool-id>
VITE_COGNITO_CLIENT_ID=<your-client-id>
EOF
```

### 4. Start Development Server

```bash
npm run dev
```

Visit http://localhost:5173

---

## Social Media Setup (10 minutes)

### Facebook

1. **Create Facebook App**
   - Go to [Facebook Developers](https://developers.facebook.com)
   - Create New App → Business
   - Add Facebook Login product

2. **Configure OAuth**
   - Settings → Basic
   - Add App Domains
   - Add Privacy Policy URL (can be placeholder for testing)

3. **Get Credentials**
   - Note App ID and App Secret
   - Add to backend secrets

### YouTube

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create New Project

2. **Enable YouTube Data API v3**
   - APIs & Services → Library
   - Search "YouTube Data API v3"
   - Click Enable

3. **Create OAuth Credentials**
   - APIs & Services → Credentials
   - Create OAuth 2.0 Client ID
   - Application type: Web application
   - Add authorized redirect URIs

### Instagram (Optional)

1. **Convert to Business Account**
   - Open Instagram app
   - Settings → Account → Switch to Professional Account
   - Choose Business

2. **Link to Facebook Page**
   - Create Facebook Page if you don't have one
   - Link Instagram Business account to Page

3. **Configure in Facebook App**
   - Facebook App → Products → Instagram
   - Add Instagram product
   - Complete setup

---

## First Post (5 minutes)

### 1. Create User Account

```bash
# Via AWS Console:
# Cognito → User Pools → ToAllCreationUsers → Users → Create user
# Set temporary password
```

### 2. Log In

- Open frontend URL
- Log in with credentials
- Change password if prompted

### 3. Connect Platforms

- Navigate to Platforms page
- Click "Connect Facebook"
- Authorize app
- Repeat for YouTube, Instagram

### 4. Create Post

- Navigate to Create Post
- Enter content: "Testing ToAllCreation! 🙏"
- Select platforms (Facebook, YouTube)
- Click "Publish Now"

### 5. Verify

- Check Facebook page
- Check YouTube community post
- Check Instagram (if connected)

---

## Troubleshooting

### Common Issues

**Issue:** `sam build` fails with "Docker not running"
```bash
# Start Docker Desktop
# Retry: sam build --use-container
```

**Issue:** OAuth redirect fails
```bash
# Verify redirect URI matches exactly
# Check: https://your-frontend-url/auth/callback
```

**Issue:** API Gateway 401 Unauthorized
```bash
# Check Cognito token in request headers
# Verify Authorization: Bearer <token>
```

**Issue:** Platform API error
```bash
# Check token validity
# Refresh access token
# Verify platform permissions
```

**Issue:** Video upload fails
```bash
# Check file size (max 500 MB recommended)
# Verify S3 CORS configuration
# Check network connection
```

### Getting Help

1. Check CloudWatch Logs (AWS Console → CloudWatch → Logs)
2. Review DynamoDB entries (AWS Console → DynamoDB → Tables)
3. Check SQS Dead Letter Queue for failed messages
4. Review error messages in browser console (F12)

---

## Next Steps

### Week 1
- [x] Complete Quick Start
- [ ] Deploy production infrastructure
- [ ] Set up CI/CD with GitHub Actions
- [ ] Implement authentication
- [ ] Create platform management UI

### Week 2-4
- [ ] Build post composer
- [ ] Implement media uploads
- [ ] Create async posting system
- [ ] Add post status tracking

### Week 5-8
- [ ] Polish UI/UX
- [ ] Mobile responsive design
- [ ] Security hardening
- [ ] Production launch

### Phase 2 (Weeks 9-12)
- [ ] Comment aggregation
- [ ] Comment dashboard
- [ ] Reply functionality
- [ ] Email notifications

---

## Key Files to Review

| File | Purpose |
|------|---------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Complete architecture design |
| [TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md) | Decisions required before starting |
| [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) | Step-by-step implementation guide |
| [README.md](./README.md) | Project overview |

---

## Cost Monitoring

### Set Up Billing Alerts

1. **AWS Budgets**
   ```bash
   # Via AWS Console:
   # Billing → Budgets → Create budget
   # Set budget: $5/month
   # Alert threshold: 80%
   ```

2. **CloudWatch Alarms**
   - Monitor S3 storage (alert at 4.5 GB)
   - Monitor Lambda invocations (alert at 900K/month)
   - Monitor DynamoDB capacity

### Expected Costs

| Period | Cost |
|--------|------|
| **First 12 months** | ~$2-3/month |
| **After 12 months** | ~$2.60/month |
| **Annual (after free tier)** | ~$31/year |

---

## Success Checklist

- [ ] Backend deployed successfully
- [ ] Frontend accessible
- [ ] User can log in
- [ ] Platforms connect successfully
- [ ] Post publishes to Facebook
- [ ] Post publishes to YouTube
- [ ] Post publishes to Instagram (if configured)
- [ ] Post status updates correctly
- [ ] Costs within budget

---

## Architecture at a Glance

```
User → CloudFront → React SPA
                 ↓
            API Gateway → Lambda (FastAPI)
                         ↓
                    DynamoDB (Data)
                    S3 (Media)
                    SQS (Queue)
                         ↓
                 Platform APIs
                 (Facebook, YouTube, Instagram)
```

---

## Development Workflow

```bash
# Backend changes
cd backend
sam build && sam deploy

# Frontend changes
cd frontend
npm run dev     # Development
npm run build   # Production build

# Deploy frontend
aws s3 sync dist/ s3://your-bucket --delete
```

---

## Essential Commands

```bash
# Backend
sam build                          # Build Lambda functions
sam deploy                         # Deploy to AWS
sam logs -n ApiFunction --tail    # View logs

# Frontend
npm run dev                        # Development server
npm run build                      # Production build
npm run preview                    # Preview build

# AWS
aws dynamodb scan --table-name ToAllCreation    # View data
aws s3 ls s3://your-bucket                      # List S3 files
aws logs tail /aws/lambda/ApiFunction           # View logs
```

---

## Resources

### Documentation
- [AWS SAM Developer Guide](https://docs.aws.amazon.com/serverless-application-model/)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [React Documentation](https://react.dev)
- [Facebook Graph API](https://developers.facebook.com/docs/graph-api)
- [YouTube Data API](https://developers.google.com/youtube/v3)

### Community
- [AWS Forums](https://forums.aws.amazon.com)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/aws-lambda)
- [Reddit r/aws](https://reddit.com/r/aws)

---

**Ready to spread the gospel? Let's build! 🚀**

*"Go into all the world and preach the gospel to all creation." - Mark 16:15*
