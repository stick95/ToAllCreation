# ToAllCreation

*"Go into all the world and preach the gospel to all creation." - Mark 16:15*

A serverless social media aggregator platform that enables gospel content creators to efficiently share their message across multiple platforms simultaneously.

---

## 🚀 Current Status: Hello World Deployed

**Live URLs:**
- **Frontend (HTTPS):** https://d1p7fiwu5m4weh.cloudfront.net
- **Frontend (S3):** http://toallcreation-frontend-271297706586.s3-website-us-west-2.amazonaws.com
- **Backend API:** https://50gms3b8y2.execute-api.us-west-2.amazonaws.com

**What's Working:**
- ✅ Full-stack Hello World application
- ✅ FastAPI backend on AWS Lambda (Python 3.12, ARM64)
- ✅ React + Vite + TypeScript frontend
- ✅ CloudFront CDN with HTTPS
- ✅ CI/CD workflows (GitHub Actions)
- ✅ All within AWS Free Tier ($0/month)

---

## 📦 Quick Start

### Test the Live Application
Visit: https://d1p7fiwu5m4weh.cloudfront.net

Click **"Test Backend API"** to verify end-to-end connectivity!

### Local Development

**Backend:**
```bash
cd backend
sam build
sam local start-api --port 3000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:5173
```

---

## 🏗️ Project Structure

```
ToAllCreation/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application
│   │   └── requirements.txt     # Python dependencies
│   ├── template.yaml            # AWS SAM template
│   └── samconfig.toml           # SAM deployment config
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main React component
│   │   └── ...
│   ├── package.json
│   └── vite.config.ts
├── .github/workflows/
│   ├── backend-deploy.yml       # Backend CI/CD
│   └── frontend-deploy.yml      # Frontend CI/CD
├── docs/                        # Full project documentation
│   ├── ARCHITECTURE.md          # Complete architecture (104 KB)
│   ├── IMPLEMENTATION_CHECKLIST.md  # Week-by-week plan
│   ├── QUICK_START.md           # 30-minute setup guide
│   └── ...
├── DEPLOYMENT.md                # Deployment guide
├── DEPLOYMENT-COMPLETE.md       # Live deployment info
├── CLOUDFRONT-INFO.md           # CloudFront CDN details
└── AWS-DEPLOYMENT-INFO.md       # AWS resources info
```

---

## 🎯 API Endpoints

All endpoints are CORS-enabled:

- **`GET /`** - Root endpoint
  ```json
  {
    "message": "ToAllCreation API - Hello World!",
    "version": "0.1.0",
    "status": "operational"
  }
  ```

- **`GET /health`** - Health check
  ```json
  {
    "status": "healthy"
  }
  ```

- **`GET /api/hello`** - Test endpoint
  ```json
  {
    "message": "Hello from the backend!",
    "timestamp": "2025-11-03",
    "service": "ToAllCreation Backend API"
  }
  ```

---

## 🔧 Tech Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **Build Tool:** Vite (fast builds, HMR)
- **State Management:** Zustand (planned)
- **UI Components:** Shadcn/ui + Tailwind CSS (planned)
- **Hosting:** S3 + CloudFront CDN

### Backend
- **Framework:** FastAPI (Python 3.12)
- **Runtime:** AWS Lambda (ARM64 Graviton2)
- **API Gateway:** HTTP API
- **Deployment:** AWS SAM

### Infrastructure
- **CDN:** CloudFront (HTTPS, global edge locations)
- **Storage:** S3 (static website hosting)
- **CI/CD:** GitHub Actions
- **Region:** us-west-2 (Oregon)

### Planned (Full MVP)
- **Database:** DynamoDB (single-table design)
- **Auth:** AWS Cognito
- **Media Storage:** S3
- **Queue:** SQS (async posting)
- **Scheduling:** EventBridge
- **Social APIs:** Facebook, YouTube, Instagram

---

## 💰 Cost Analysis

**Current (Hello World):**
- Lambda: $0 (1M requests/month free)
- API Gateway: $0 (1M requests/month free for 12 months)
- S3: $0 (5GB storage free for 12 months)
- CloudFront: $0 (1TB transfer/month free)
- **Total: $0/month** ✅

**Full MVP Estimate:**
- First 12 months: ~$2-3/month
- After 12 months: ~$2.60/month
- Optimized: ~$0.60/month (with SSM instead of Secrets Manager)

---

## 🚀 Deployment

### Deploy Backend
```bash
cd backend
sam build --use-container
sam deploy
```

### Deploy Frontend
```bash
cd frontend
npm run build
aws s3 sync dist/ s3://toallcreation-frontend-271297706586/ --delete
aws cloudfront create-invalidation --distribution-id E2JDMDOIC3T6K6 --paths "/*"
```

### CI/CD (Automatic)
Push to `main` branch triggers automatic deployment via GitHub Actions.

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `VITE_API_URL`
- `S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID`

---

## 📚 Documentation

### Quick Reference
- **[docs/DEPLOYMENT-COMPLETE.md](./docs/DEPLOYMENT-COMPLETE.md)** - Current deployment status
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)** - Step-by-step deployment guide
- **[docs/CLOUDFRONT-INFO.md](./docs/CLOUDFRONT-INFO.md)** - CDN configuration & cache busting
- **[docs/AWS-DEPLOYMENT-INFO.md](./docs/AWS-DEPLOYMENT-INFO.md)** - AWS resources details
- **[docs/HELLO-WORLD-SUMMARY.md](./docs/HELLO-WORLD-SUMMARY.md)** - Implementation summary

### Full Project Documentation
- **[docs/INDEX.md](./docs/INDEX.md)** - Documentation navigation
- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - Complete technical architecture
- **[docs/IMPLEMENTATION_CHECKLIST.md](./docs/IMPLEMENTATION_CHECKLIST.md)** - Week-by-week implementation plan
- **[docs/QUICK_START.md](./docs/QUICK_START.md)** - 30-minute setup guide
- **[docs/TECHNICAL_DECISIONS.md](./docs/TECHNICAL_DECISIONS.md)** - Key decisions to make

---

## 🎯 Roadmap

### ✅ Phase 0: Hello World (Complete)
- [x] Backend API with FastAPI + Lambda
- [x] Frontend with React + Vite
- [x] S3 static hosting
- [x] CloudFront CDN with HTTPS
- [x] CI/CD pipelines
- [x] Full AWS deployment

### 📋 Phase 1: MVP (Weeks 1-8)
**Goal:** Single-user posting to multiple platforms

**Week 1-2:** Foundation & Infrastructure
- [ ] DynamoDB table setup
- [ ] Cognito authentication
- [ ] Basic frontend layout

**Week 3-4:** Authentication & Core API
- [ ] User login/logout
- [ ] Platform OAuth integration (Facebook, YouTube)
- [ ] Credentials management

**Week 5-6:** Post Management
- [ ] Post creation UI
- [ ] Media upload (S3 pre-signed URLs)
- [ ] SQS async posting
- [ ] Status tracking

**Week 7-8:** Polish & Launch
- [ ] Error handling
- [ ] Responsive design
- [ ] Production deployment
- [ ] User testing

### 📋 Phase 2: Comment Aggregation (Weeks 9-12)
- [ ] Comment polling (EventBridge)
- [ ] Comment dashboard
- [ ] Reply functionality
- [ ] Email notifications

### 🔮 Phase 3: Future Enhancements
- [ ] Scheduled posting
- [ ] Analytics dashboard
- [ ] Multi-user support
- [ ] Mobile apps (Flutter)
- [ ] LinkedIn & TikTok support
- [ ] AI content suggestions

---

## 🧪 Testing

### Test Backend Locally
```bash
cd backend
sam build
sam local start-api --port 3000
curl http://localhost:3000/health
```

### Test Frontend Locally
```bash
cd frontend
npm run dev
# Visit http://localhost:5173
```

### Test Deployed API
```bash
curl https://50gms3b8y2.execute-api.us-west-2.amazonaws.com/health
```

### Test Deployed Frontend
Visit: https://d1p7fiwu5m4weh.cloudfront.net

---

## 🔐 Environment Variables

### Backend
Set in `backend/template.yaml` or Lambda console:
- (None required for Hello World)

### Frontend
Create `frontend/.env.local`:
```env
# For AWS deployment
VITE_API_URL=https://50gms3b8y2.execute-api.us-west-2.amazonaws.com

# For local backend testing
# VITE_API_URL=http://localhost:3000
```

---

## 🤝 Contributing

This is currently a single-developer project. Contributions welcome after MVP launch.

### Development Workflow
1. Create feature branch from `dev`
2. Make changes
3. Test locally
4. Merge to `dev`
5. Test on `dev` branch
6. Merge to `main` for production deployment

---

## 📊 Monitoring

### CloudWatch Logs
```bash
sam logs -n ApiFunction --stack-name toallcreation-backend --tail
```

### CloudFront Metrics
```bash
aws cloudfront get-distribution --id E2JDMDOIC3T6K6 --query 'Distribution.Status'
```

### AWS Console
- **Lambda:** https://us-west-2.console.aws.amazon.com/lambda
- **API Gateway:** https://us-west-2.console.aws.amazon.com/apigateway
- **CloudFront:** https://console.aws.amazon.com/cloudfront
- **S3:** https://s3.console.aws.amazon.com/s3/buckets/toallcreation-frontend-271297706586

---

## 🗑️ Cleanup

### Delete All AWS Resources
```bash
# Delete CloudFront (must disable first, takes 15 min)
aws cloudfront get-distribution-config --id E2JDMDOIC3T6K6 > /tmp/cf.json
# Edit: Set "Enabled": false, then update and delete

# Delete backend stack
aws cloudformation delete-stack --stack-name toallcreation-backend --region us-west-2

# Delete S3 bucket
aws s3 rm s3://toallcreation-frontend-271297706586/ --recursive
aws s3 rb s3://toallcreation-frontend-271297706586
```

---

## 📝 License

Private project - All rights reserved

---

## 🙏 Mission

This platform exists to empower gospel content creators to efficiently spread the message of Jesus Christ across multiple social media platforms, maximizing reach and minimizing effort.

*"Therefore go and make disciples of all nations..." - Matthew 28:19*

---

## 📞 Contact

For questions or feedback, please open an issue in the GitHub repository.

---

**Status:** ✅ Hello World Complete | 🚧 MVP In Planning
