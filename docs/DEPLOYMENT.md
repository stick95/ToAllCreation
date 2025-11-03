# ToAllCreation - Deployment Guide

Simple Hello World deployment for testing CI/CD pipelines.

## Quick Start

### Prerequisites

- AWS Account configured (`aws configure`)
- AWS SAM CLI installed
- Node.js 20+ installed
- Docker installed (for SAM builds)

## Local Development

### Backend (FastAPI + SAM)

```bash
cd backend
sam build
sam local start-api --port 3000
```

Test: `curl http://localhost:3000/api/hello`

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

Click "Test Backend API" to verify integration.

## AWS Deployment

### 1. Deploy Backend

```bash
cd backend
sam build --use-container
sam deploy --guided
```

On first deployment, you'll be prompted for:
- Stack name: `toallcreation-backend`
- Region: `us-east-1`
- Confirm changes: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments: `Y`

**Important:** Note the API Gateway URL from the outputs:
```
Outputs:
  ApiUrl: https://abc123.execute-api.us-east-1.amazonaws.com
```

### 2. Update Frontend Environment

```bash
cd frontend
cp .env.example .env.local
```

Edit `.env.local`:
```
VITE_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

### 3. Deploy Frontend (Manual for now)

```bash
cd frontend
npm run build

# Upload to S3 (create bucket first)
aws s3 mb s3://toallcreation-frontend-YOUR-ACCOUNT-ID
aws s3 sync dist/ s3://toallcreation-frontend-YOUR-ACCOUNT-ID/
aws s3 website s3://toallcreation-frontend-YOUR-ACCOUNT-ID/ --index-document index.html
```

## CI/CD Setup

### GitHub Secrets Required

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `VITE_API_URL` - Your API Gateway URL
- `S3_BUCKET` - Your S3 bucket name (for frontend)
- `CLOUDFRONT_DISTRIBUTION_ID` - Your CloudFront ID (optional)

### Workflows

Two workflows are configured:

1. **Backend Deploy** (`.github/workflows/backend-deploy.yml`)
   - Triggers on push to `main` with changes in `backend/`
   - Runs `sam build` and `sam deploy`

2. **Frontend Deploy** (`.github/workflows/frontend-deploy.yml`)
   - Triggers on push to `main` with changes in `frontend/`
   - Builds frontend and deploys to S3
   - Invalidates CloudFront cache (optional)

## Testing the Deployment

1. **Test Backend API:**
   ```bash
   curl https://your-api-id.execute-api.us-east-1.amazonaws.com/api/hello
   ```

   Expected response:
   ```json
   {
     "message": "Hello from the backend!",
     "timestamp": "2025-11-03",
     "service": "ToAllCreation Backend API"
   }
   ```

2. **Test Frontend:**
   - Visit your S3 website URL or CloudFront distribution
   - Click "Test Backend API" button
   - Should see the JSON response displayed

## Architecture

```
Frontend (React + Vite)
  ↓
API Gateway (HTTP API)
  ↓
Lambda (FastAPI + Mangum)
```

## Costs

This Hello World setup uses:
- Lambda: Free tier (1M requests/month)
- API Gateway: Free tier (1M requests/month for 12 months)
- S3: Free tier (5GB storage)

**Estimated cost:** $0/month within free tier

## Next Steps

After verifying Hello World works:

1. Add authentication (AWS Cognito)
2. Add database (DynamoDB)
3. Add media storage (S3)
4. Add async processing (SQS + Lambda)
5. Follow full implementation from `docs/IMPLEMENTATION_CHECKLIST.md`

## Troubleshooting

### Backend won't build
```bash
# Make sure Docker is running
docker ps

# Try building with container
sam build --use-container
```

### Frontend can't reach backend
- Check CORS configuration in `backend/template.yaml`
- Verify `VITE_API_URL` in `.env.local`
- Check browser console for errors

### SAM deploy fails
```bash
# Delete existing stack and redeploy
aws cloudformation delete-stack --stack-name toallcreation-backend
sam deploy --guided
```

## Commands Reference

```bash
# Backend
cd backend
sam build                     # Build Lambda
sam local start-api          # Test locally
sam deploy                    # Deploy to AWS
sam logs -n ApiFunction      # View logs

# Frontend
cd frontend
npm run dev                   # Dev server
npm run build                 # Production build
npm run preview               # Preview build

# AWS
aws cloudformation describe-stacks --stack-name toallcreation-backend
aws lambda invoke --function-name toallcreation-ApiFunction response.json
```
